#!/bin/bash

# Plaza Apartment Scraper VPS Setup Script
# This script sets up PM2, Python dependencies, and monitoring dashboard

echo "🚀 Setting up Plaza Apartment Scraper on VPS..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python3 and pip if not already installed
echo "🐍 Installing Python3 and pip..."
sudo apt install -y python3 python3-pip python3-venv

# Install Node.js and npm (required for PM2)
echo "📦 Installing Node.js and npm..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install PM2 globally
echo "⚡ Installing PM2..."
sudo npm install -g pm2

# Install PM2 log rotate module (optional but recommended)
sudo pm2 install pm2-logrotate

# Create logs directory
echo "📁 Creating logs directory..."
mkdir -p logs

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip3 install -r requirements.txt

# Create .env file template if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env template..."
    cat > .env << EOL
# Discord Webhook URL for notifications
DISCORD_WEBHOOK_URL=your_discord_webhook_url_here
EOL
    echo "⚠️  Please edit .env file with your actual Discord webhook URL"
fi

# Set up PM2 startup script (so it starts on boot)
echo "🔧 Setting up PM2 startup script..."
sudo pm2 startup
echo "ℹ️  You may need to run the command that PM2 outputs above"

# Update ecosystem.config.js with current directory
echo "📝 Updating ecosystem config with current directory..."
CURRENT_DIR=$(pwd)
sed -i "s|/path/to/your/scraper|$CURRENT_DIR|g" ecosystem.config.js

echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your Discord webhook URL"
echo "2. Run: pm2 start ecosystem.config.js"
echo "3. Run: pm2 save (to save current PM2 configuration)"
echo "4. Set up PM2 Plus monitoring (optional):"
echo "   - Visit: https://app.pm2.io/"
echo "   - Create account and get your secret/public keys"
echo "   - Run: pm2 link <secret_key> <public_key>"
echo ""
echo "🔍 Useful PM2 commands:"
echo "  pm2 list                 - Show running processes"
echo "  pm2 logs plaza-scraper   - Show logs"
echo "  pm2 restart plaza-scraper - Restart the scraper"
echo "  pm2 stop plaza-scraper   - Stop the scraper"
echo "  pm2 monit               - Open monitoring dashboard" 