# Plaza Apartment Scraper - AWS Lambda Deployment

This document provides instructions for deploying the Plaza apartment scraper to AWS Lambda for serverless operation.

## Prerequisites

1. [AWS CLI](https://aws.amazon.com/cli/) installed and configured with appropriate credentials
2. [Python 3.9+](https://www.python.org/downloads/)
3. Your Discord webhook URL

## Files Overview

- `lambda_scraper.py`: The main Lambda function code
- `requirements-lambda.txt`: Python dependencies
- `cloudformation-template.yml`: AWS CloudFormation template
- `deploy.sh`: Deployment script

## Deployment Steps

### 1. Update Configuration (Optional)

- Open `deploy.sh` to update the region and deployment bucket name if needed.

### 2. Run the Deployment Script

```bash
./deploy.sh
```

When prompted, enter your Discord webhook URL.

### 3. Verify Deployment

1. Visit the [AWS Lambda Console](https://console.aws.amazon.com/lambda)
2. Select your region
3. Look for the `plaza-scraper-function` function
4. Check the CloudWatch logs to verify it's running properly

## How It Works

After deployment:

1. The Lambda function runs every 5 minutes using CloudWatch Events
2. It checks for new apartment listings in Enschede from the Plaza API
3. It stores previously seen listing IDs in S3
4. It sends Discord notifications for any new listings found

## Monitoring and Maintenance

### Viewing Logs

```bash
aws logs get-log-events \
  --log-group-name /aws/lambda/plaza-scraper-function \
  --log-stream-name $(aws logs describe-log-streams \
    --log-group-name /aws/lambda/plaza-scraper-function \
    --order-by LastEventTime \
    --descending \
    --max-items 1 \
    --query 'logStreams[0].logStreamName' \
    --output text)
```

### Updating the Function

If you need to update the code, simply run the `deploy.sh` script again.

### Cleaning Up Resources

To delete all created resources when no longer needed:

```bash
aws cloudformation delete-stack \
  --stack-name plaza-scraper-stack \
  --region eu-west-1
```

## Troubleshooting

1. **Lambda Timeouts**: If the function times out, increase the timeout in the CloudFormation template.
2. **Missing Permissions**: Ensure the Lambda role has permissions to access CloudWatch Logs and S3.
3. **Dependency Issues**: If Lambda fails due to missing dependencies, ensure all required packages are in `requirements-lambda.txt`.

## Cost Considerations

AWS Lambda offers a generous free tier:
- 1 million free requests per month
- 400,000 GB-seconds of compute time per month

At 5-minute intervals, the scraper will run approximately 8,640 times per month, which should remain within the free tier if execution is kept lightweight. 