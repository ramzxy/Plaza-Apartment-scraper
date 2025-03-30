#!/usr/bin/env python3
"""
Test script to run the Lambda function locally.
This script simulates the Lambda environment by providing mock event and context objects.
"""

import os
import json
from AWS.lambda_scraper import lambda_handler

# Check for Discord webhook URL
if 'DISCORD_WEBHOOK_URL' not in os.environ:
    print("ERROR: DISCORD_WEBHOOK_URL environment variable not set.")
    print("Please set it first:")
    print("export DISCORD_WEBHOOK_URL=your_discord_webhook_url")
    exit(1)

# Create a mock S3 bucket name (will be replaced by the actual function, but needs to be set)
os.environ['S3_BUCKET_NAME'] = 'mock-bucket-local-testing'

# Create a mock event (empty for this function as it doesn't use the event)
event = {}

# Create a mock context object
class MockContext:
    def __init__(self):
        self.function_name = "local-test"
        self.memory_limit_in_mb = 128
        self.invoked_function_arn = "arn:aws:lambda:local:123456789012:function:local-test"
        self.aws_request_id = "local-test-id"
        
    def get_remaining_time_in_millis(self):
        return 300000  # 5 minutes

# Run the Lambda function
print("Starting local test of Lambda function...")
context = MockContext()
result = lambda_handler(event, context)

# Print the result
print("\nExecution complete. Result:")
print(json.dumps(result, indent=2)) 