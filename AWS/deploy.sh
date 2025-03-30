#!/bin/bash
set -e

# Configuration
STACK_NAME="plaza-scraper-stack"
REGION="eu-west-1"  # Change to your preferred region
PACKAGE_OUTPUT_PATH="package.zip"
DEPLOYMENT_BUCKET_NAME="plaza-scraper-deployment-bucket"  # Change to your actual bucket name
DISCORD_WEBHOOK_URL=""  # Will prompt for this if empty

# Ensure AWS CLI is available
command -v aws > /dev/null || { echo "AWS CLI is required but not installed. Aborting."; exit 1; }

# Ask for Discord webhook URL if not provided
if [ -z "$DISCORD_WEBHOOK_URL" ]; then
    read -p "Enter your Discord webhook URL: " DISCORD_WEBHOOK_URL
fi

echo "🔍 Creating package directory..."
mkdir -p package

echo "📦 Installing dependencies..."
pip install -r requirements-lambda.txt --target ./package

echo "📝 Copying code files..."
cp lambda_scraper.py ./package/

echo "🗜️ Creating ZIP package..."
cd package
zip -r ../$PACKAGE_OUTPUT_PATH .
cd ..

echo "🧹 Cleaning up package directory..."
rm -rf package

# Check if deployment bucket exists, create if it doesn't
if ! aws s3 ls "s3://$DEPLOYMENT_BUCKET_NAME" --region $REGION > /dev/null 2>&1; then
    echo "🪣 Creating deployment bucket..."
    aws s3 mb "s3://$DEPLOYMENT_BUCKET_NAME" --region $REGION
fi

echo "☁️ Uploading package to S3..."
aws s3 cp $PACKAGE_OUTPUT_PATH "s3://$DEPLOYMENT_BUCKET_NAME/" --region $REGION

echo "🚀 Deploying CloudFormation stack..."
aws cloudformation deploy \
    --template-file cloudformation-template.yml \
    --stack-name $STACK_NAME \
    --parameter-overrides \
        DiscordWebhookUrl=$DISCORD_WEBHOOK_URL \
    --capabilities CAPABILITY_IAM \
    --region $REGION

echo "📊 Updating Lambda function code..."
FUNCTION_NAME=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query "Stacks[0].Outputs[?OutputKey=='PlazaScraperFunctionArn'].OutputValue" --output text | awk -F: '{print $NF}')

aws lambda update-function-code \
    --function-name $FUNCTION_NAME \
    --s3-bucket $DEPLOYMENT_BUCKET_NAME \
    --s3-key $PACKAGE_OUTPUT_PATH \
    --region $REGION

echo "✅ Deployment completed successfully! Your Plaza apartment scraper is now running in AWS Lambda."
echo "✅ It will check for new listings every 5 minutes and send notifications to Discord." 