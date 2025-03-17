# Purpose: This file is used to create the Lambda function that will transform the data and send it to Loki.

data "archive_file" "python_lambda_package" {
  type        = "zip"
  source_file = "./transform_send_events_loki.py"
  output_path = "transform_send_events_loki.zip"
}

resource "aws_lambda_function" "transform_app_events" {
  function_name    = "transform_send_events_loki"
  filename         = "transform_send_events_loki.zip"
  source_code_hash = data.archive_file.python_lambda_package.output_base64sha256
  role             = aws_iam_role.lambda_role.arn
  runtime          = "python3.12"
  handler          = "transform_send_events_loki.lambda_handler"
  timeout          = 60
  environment {
    variables = {
      LOKI_URL            = "http://ec2-ip.compute-1.amazonaws.com:3100/loki/api/v1/push"
      KINESIS_STREAM_NAME = aws_kinesis_stream.data_stream.name
    }
  }
  layers = [
    aws_lambda_layer_version.requests_layer.arn
  ]
  depends_on = [
    aws_cloudwatch_log_group.data-transform-group,
  ]
}

resource "aws_lambda_layer_version" "requests_layer" {
  layer_name          = "requests-layer"
  description         = "A Lambda layer that includes the requests module"
  compatible_runtimes = ["python3.8", "python3.9", "python3.10", "python3.12"]

  filename = "./requests-layer.zip"

  source_code_hash = filebase64sha256("./requests-layer.zip")
}