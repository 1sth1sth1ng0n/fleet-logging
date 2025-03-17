# Purpose: Create a Kinesis stream to store data from the application and a CloudWatch log group to store the data.
# The Kinesis stream is used to trigger the lambda function when new data is added to the stream.

resource "aws_kinesis_stream" "data_stream" {
  name             = "my-data-stream"
  shard_count      = 1
  retention_period = 24 # Retain data for 24 hours
}

resource "aws_lambda_event_source_mapping" "kinesis_trigger" {
  event_source_arn  = aws_kinesis_stream.data_stream.arn
  function_name     = aws_lambda_function.transform_app_events.arn
  starting_position = "LATEST"
}