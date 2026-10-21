# Plaza Apartment Scraper

A lightweight scraper for monitoring new apartment listings on Plaza and sending Discord and/or Telegram notifications.

## Features

- Monitors available apartments in Enschede from Plaza website
- Uses direct API integration with exact filter payload matching the website
- Makes POST requests with the precise filters used by the website itself
- Sends Discord and/or Telegram notifications for new listings
- Runs in a lightweight manner, suitable for VPS deployment

## How It Works

The scraper makes a direct POST request to the Plaza API with specific filter parameters:
- Uses exact municipality ID for Enschede (15897)
- Filters for Overijssel region (ID: 9)
- Focuses on rental properties (not for sale)
- Uses the same API endpoint and filters as the official website

## Setup

1. Clone this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project directory with your notification settings (Discord, Telegram, or both):
   ```
   # Discord (optional)
   PLAZA_WEBHOOK_URL=your_plaza_discord_webhook_url_here
   ROOMSPOT_WEBHOOK_URL=your_roomspot_discord_webhook_url_here

   # Telegram (optional)
   TELEGRAM_BOT_TOKEN=123456789:your_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   ```

### Telegram setup

1. Open a chat with [@BotFather](https://t.me/BotFather), send `/newbot`, and copy the bot token into `TELEGRAM_BOT_TOKEN`.
2. Send any message to your new bot (or add it to a group).
3. Open `https://api.telegram.org/bot<TOKEN>/getUpdates` and copy `message.chat.id` into `TELEGRAM_CHAT_ID`.

## Usage

Run the scraper:

```
python scraper.py
```

The scraper will check for new listings every 5 minutes and send notifications via Discord and/or Telegram.

## Running in the Background

To run the scraper continuously in the background:

### Using Screen (Linux/Mac)

1. Install screen:
   ```
   # Ubuntu/Debian
   sudo apt-get install screen
   
   # MacOS
   brew install screen
   ```

2. Start a new screen session:
   ```
   screen -S plaza-scraper
   ```

3. Run the scraper:
   ```
   python scraper.py
   ```

4. Detach from the screen session by pressing `Ctrl+A` followed by `D`
5. To reattach to the session later:
   ```
   screen -r plaza-scraper
   ```

### Using Systemd (Linux)

1. Create a systemd service file:
   ```
   sudo nano /etc/systemd/system/plaza-scraper.service
   ```

2. Add the following content (adjust paths as needed):
   ```
   [Unit]
   Description=Plaza Apartment Scraper
   After=network.target

   [Service]
   User=your_username
   WorkingDirectory=/path/to/scraper
   ExecStart=/usr/bin/python3 /path/to/scraper/scraper.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start the service:
   ```
   sudo systemctl enable plaza-scraper
   sudo systemctl start plaza-scraper
   ```

4. Check the status:
   ```
   sudo systemctl status plaza-scraper
   ```

## Requirements

- Python 3.6+
- requests
- discord.py
- python-dotenv
- aiohttp

## License

This project is for personal use only. 