# Purpose: Create CloudWatch log groups and streams for the Kinesis Firehose and Lambda functions.

resource "aws_cloudwatch_log_group" "fleet-data-log" {
  name              = "/aws/kinesisfirehose/fleet-kinesis-stream"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_stream" "fleet-data-stream" {
  name           = "DestinationDelivery"
  log_group_name = aws_cloudwatch_log_group.fleet-data-log.name
}

resource "aws_cloudwatch_log_group" "data-transform-group" {
  name              = "/aws/lambda/fleet-transform-app-events"
  retention_in_days = 7
}