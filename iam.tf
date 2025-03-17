# Purpose: This file is used to create IAM roles and policies for the lambda function and the kinesis stream.
# The IAM roles and policies are used to give the lambda function the necessary permissions to interact with the kinesis stream.

data "aws_iam_policy_document" "kinesis-logging" {
  statement {
    actions = [
      "kinesis:DescribeStream",
      "kinesis:PutRecord",
      "kinesis:PutRecords"
    ]
    resources = [
      aws_kinesis_stream.data_stream.arn
    ]
  }
}

resource "aws_iam_policy" "kinesis-logging" {
  description = "An IAM policy for fleet to log to Firehose destinations"
  policy      = data.aws_iam_policy_document.kinesis-logging.json
}

data "aws_iam_policy_document" "data_transform_policy_doc" {
  statement {
    effect = "Allow"
    actions = [
      "logs:PutLogEvents",
      "cloudwatch:GenerateQuery",
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
    ]

    resources = [
      "arn:aws:logs:*:*:*",
    ]
  }
  statement {
    actions = [
      "kinesis:DescribeStream",
      "kinesis:GetRecords",
      "kinesis:GetShardIterator",
      "kinesis:ListStreams"
    ]
    resources = [aws_kinesis_stream.data_stream.arn]
  }
}

data "aws_iam_policy_document" "lambda_assume_role_policy" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_policy" "data_transform_policy" {
  name   = "fleet_lambda_policy"
  policy = data.aws_iam_policy_document.data_transform_policy_doc.json
}

resource "aws_iam_role" "lambda_role" {
  name               = "fleet_lambda_role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role_policy.json
}

resource "aws_iam_role_policy_attachment" "data_transform" {
  policy_arn = aws_iam_policy.data_transform_policy.arn
  role       = aws_iam_role.lambda_role.name
}