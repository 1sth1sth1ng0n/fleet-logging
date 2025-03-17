import json
import base64
import os
import requests
from datetime import datetime, timezone

"""
====================================
||     Kinesis to Loki Logger     ||
====================================
Date:         20241912
Version:      1.0
Description:  Processing logs from AWS Kinesis streams and forwarding them 
              to Loki for centralized log aggregation.

Environment Variables:
  - LOKI_URL:            URL of the Loki instance.
  - KINESIS_STREAM_NAME: Name of the Kinesis stream.

Dependencies:
  - Python >= 3.8
  - Requests library for HTTP communication.

Usage:
  Deployed as an AWS Lambda function. It listens to Kinesis 
  streams, decodes base64-encoded log records, and forwards structured logs 
  to Loki in the proper payload format.

License:
  None

====================================
"""

# function to send logs to loki
# accepts loki url and logs in json format
def send_logs_to_loki(loki_url, logs):
    headers = {'Content-Type': 'application/json'}
    response = requests.post(loki_url, data=json.dumps(logs), headers=headers)
    print(f"Sending logs to loki: {loki_url}")
    #print(f"Preparing to send logs: {json.dumps(logs)}")  # used for debug in cloudwatch logs
    if response.status_code == 204:
        print("logs successfully sent to loki.")
    else:
        print(f"failed to send logs: {response.status_code}, response: {response.text}")

# function to prepare logs for loki
# converts incoming log data into the payload format required by loki
def prepare_loki_payload(data):
    # retrieve kinesis stream name from environment variables
    kinesis_stream_name = os.environ.get("KINESIS_STREAM_NAME", "unknown_stream")

    hostname = str(data["decorations"]["hostname"])  # extract hostname
    host_uuid = str(data["decorations"]["host_uuid"])  # extract host uuid
    # generate a timestamp in nanoseconds for loki
    timestamp = str(int(datetime.now(timezone.utc).timestamp() * 1_000_000_000))  

    logs = []  # initialize an empty list to store the prepared logs
    for entry in data["snapshot"]:  # iterate over all snapshot entries
        bundle_identifier = entry.get("bundle_identifier")  # get the bundle identifier
        if bundle_identifier:  # only process entries with a valid bundle identifier
            # prepare a log message
            log_message = {
                "host": hostname,
                "host_uuid": host_uuid,
                "bundle_executable": entry.get("bundle_executable"),
                "bundle_identifier": bundle_identifier,
                "bundle_name": entry.get("bundle_name"),
                "bundle_short_version": entry.get("bundle_short_version"),
                "bundle_version": entry.get("bundle_version"),
                "display_name": entry.get("display_name"),
                "name": entry.get("name"),
                "path": entry.get("path"),
                "last_opened_time": entry.get("last_opened_time")
            }
            # create a loki stream with labels and values
            stream = {
                "stream": {
                    "host": hostname,
                    "host_uuid": host_uuid,
                    "bundle_executable": entry.get("bundle_executable"),
                    "bundle_identifier": bundle_identifier,
                    "bundle_name": entry.get("bundle_name"),
                    "bundle_version": entry.get("bundle_version"),
                    "path": entry.get("path"),
                    "service_name": kinesis_stream_name
                },
                "values": [
                    [timestamp, json.dumps(log_message)]  # attach the log message to the stream
                ]
            }
            logs.append(stream)  # add the stream to the logs list

    return {"streams": logs}  # return the formatted payload

# main lambda handler function
def lambda_handler(event, context):
    # retrieve loki url from environment variables
    loki_url = os.environ.get("LOKI_URL", "")
    if not loki_url:  # check if the loki url is not set
        print("error: loki url is not set in environment variables.")
        return {
            'statusCode': 500,
            'body': json.dumps('error: loki url is not set.')
        }

    try:
        # process each record in the kinesis event
        for record in event['Records']:
            try:
                raw_data = record['kinesis']['data']  # extract the base64-encoded data
                decoded_data = base64.b64decode(raw_data).decode('utf-8')  # decode the data
                #print(f"decoded data: {decoded_data}") # used for debug in cloudwatch logs

                # handle multiple json objects separated by newlines
                lines = decoded_data.strip().split('\n')
                for line in lines:
                    if line.strip():  # ignore empty lines
                        payload = json.loads(line)  # parse the json object
                        logs = prepare_loki_payload(payload)  # prepare the logs for loki
                        send_logs_to_loki(loki_url, logs)  # send the logs to loki

            except Exception as e:  # handle record-level errors
                print(f"error processing record: {e}")
                continue  # skip to the next record

        # return success response if all records are processed
        return {
            'statusCode': 200,
            'body': json.dumps('logs processed successfully.')
        }

    except Exception as e:  # handle top-level errors
        print(f"error processing event: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'error processing event: {e}')
        }