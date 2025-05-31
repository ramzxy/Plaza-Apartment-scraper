import os
import time
import json
import requests
from dotenv import load_dotenv
import discord
from discord import Webhook
import aiohttp
import asyncio
import re
import traceback
import urllib.parse

# Load environment variables
load_dotenv()

# Constants
CHECK_INTERVAL = 1500  # 5 minutes

# Discord webhook URLs
PLAZA_WEBHOOK_URL = os.getenv('PLAZA_WEBHOOK_URL')
ROOMSPOT_WEBHOOK_URL = os.getenv('ROOMSPOT_WEBHOOK_URL')

# Scraper configurations
SCRAPERS = {
    'plaza': {
        'name': 'Plaza',
        'api_url': "https://mosaic-plaza-aanbodapi.zig365.nl/api/v1/actueel-aanbod?limit=60&locale=en_GB&page=0&sort=%2BreactionData.aangepasteTotaleHuurprijs",
        'webhook_url': PLAZA_WEBHOOK_URL,
        'base_url': 'https://plaza.newnewnew.space',
        'color': discord.Color.blue(),
        'emoji': '🏢',
        'seen_file': 'seen_listings_plaza.json'
    },
    'roomspot': {
        'name': 'Roomspot',
        'api_url': "https://studentenenschede-aanbodapi.zig365.nl/api/v1/actueel-aanbod?limit=60&locale=en_GB&page=0&sort=%2BreactionData.aangepasteTotaleHuurprijs",
        'webhook_url': ROOMSPOT_WEBHOOK_URL,
        'base_url': 'https://www.roomspot.nl',
        'color': discord.Color.green(),
        'emoji': '🏠',
        'seen_file': 'seen_listings_roomspot.json'
    }
}

# API payloads for each scraper
PLAZA_PAYLOAD = {
    "filters": {
        "$and": [
            {
                "$and": [
                    {"municipality.id": {"$eq": "15897"}},  # Enschede municipality ID
                    {"regio.id": {"$eq": "9"}},            # Overijssel region ID
                    {"land.id": {"$eq": "524"}}            # Netherlands country ID
                ]
            }
        ]
    },
    "hidden-filters": {
        "$and": [
            {"dwellingType.categorie": {"$eq": "woning"}},
            {"rentBuy": {"$eq": "Huur"}},
            {"isExtraAanbod": {"$eq": ""}},
            {"isWoningruil": {"$eq": ""}},
            {
                "$and": [
                    {
                        "$or": [
                            {"street": {"$like": ""}},
                            {"houseNumber": {"$like": ""}},
                            {"houseNumberAddition": {"$like": ""}}
                        ]
                    },
                    {
                        "$or": [
                            {"street": {"$like": ""}},
                            {"houseNumber": {"$like": ""}},
                            {"houseNumberAddition": {"$like": ""}}
                        ]
                    }
                ]
            }
        ]
    }
}

ROOMSPOT_PAYLOAD = {
    "hidden-filters": {
        "$and": [
            {"dwellingType.categorie": {"$eq": "woning"}},
            {"rentBuy": {"$eq": "Huur"}},
            {"isExtraAanbod": {"$eq": ""}},
            {"isWoningruil": {"$eq": ""}},
            {
                "$and": [
                    {
                        "$or": [
                            {"street": {"$like": ""}},
                            {"houseNumber": {"$like": ""}},
                            {"houseNumberAddition": {"$like": ""}}
                        ]
                    },
                    {
                        "$or": [
                            {"street": {"$like": ""}},
                            {"houseNumber": {"$like": ""}},
                            {"houseNumberAddition": {"$like": ""}}
                        ]
                    }
                ]
            }
        ]
    }
}

# Headers to mimic a browser request
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
    'Content-Type': 'application/json'
}

async def get_plaza_listings():
    """Fetch listings from the Plaza API."""
    listings = []
    
    try:
        print("🏢 Fetching Plaza listings...")
        async with aiohttp.ClientSession() as session:
            headers = HEADERS.copy()
            headers.update({
                'Referer': 'https://plaza.newnewnew.space/en/availables-places/living-place',
                'Origin': 'https://plaza.newnewnew.space'
            })
            
            async with session.post(
                SCRAPERS['plaza']['api_url'], 
                headers=headers,
                json=PLAZA_PAYLOAD
            ) as response:
                if response.status != 200:
                    print(f"Error: Plaza API returned status code {response.status}")
                    return listings
                
                data = await response.json()
                
                if data and 'data' in data:
                    items = data['data']
                    print(f"Plaza API returned {len(items)} items")
                    
                    for item in items:
                        try:
                            listing_id = str(item.get('id', ''))
                            
                            # Extract address components
                            street = item.get('street', '')
                            house_number = item.get('houseNumber', '')
                            house_number_addition = item.get('houseNumberAddition', '')
                            
                            # Get city info
                            city_name = ''
                            if isinstance(item.get('city'), dict):
                                city_name = item['city'].get('name', '')
                            else:
                                city_name = item.get('city', '')
                            
                            postal_code = item.get('postalcode', '')
                            
                            # Format the title
                            title_parts = [p for p in [street, house_number, house_number_addition] if p]
                            title = f"{' '.join(title_parts)}"
                            if postal_code or city_name:
                                title += f", {postal_code} {city_name}".strip()
                            
                            # Extract other details
                            price = ''
                            if item.get('totalRent'):
                                price = f"€{float(item['totalRent']):.2f}"
                            elif item.get('netRent'):
                                price = f"€{float(item['netRent']):.2f}"
                            else:
                                price = 'No price info'
                            
                            area = ''
                            if item.get('areaDwelling'):
                                area = f"{item['areaDwelling']} m²"
                            else:
                                area = 'No area info'
                            
                            property_type = ''
                            if isinstance(item.get('dwellingType'), dict):
                                property_type = item['dwellingType'].get('name', '')
                            else:
                                property_type = item.get('objectType', '')
                            
                            floor = ''
                            if isinstance(item.get('floor'), dict):
                                floor = item['floor'].get('name', '')
                            
                            # Extract image URL
                            img_url = ''
                            if item.get('pictures') and len(item['pictures']) > 0:
                                if isinstance(item['pictures'][0], dict) and 'url' in item['pictures'][0]:
                                    img_url = item['pictures'][0]['url']
                                elif isinstance(item['pictures'][0], dict) and 'uri' in item['pictures'][0]:
                                    img_url = item['pictures'][0]['uri']
                            
                            if img_url and not img_url.startswith(('http://', 'https://')):
                                img_url = f"https://plaza.newnewnew.space{img_url}"
                            
                            # Create link
                            cleaned_title = re.sub(r'[^a-z0-9]', '-', title.lower())
                            cleaned_title = re.sub(r'-+', '-', cleaned_title).strip('-')
                            
                            link = f"https://plaza.newnewnew.space/en/availables-places/living-place/details/{listing_id}"
                            if cleaned_title:
                                link += f"-{cleaned_title}"
                            
                            if not title or title.isspace():
                                continue
                            
                            listing = {
                                'id': listing_id,
                                'title': title,
                                'price': price,
                                'area': area,
                                'property_type': property_type,
                                'floor': floor,
                                'link': link,
                                'img_url': img_url,
                                'publication_date': item.get('publicationDate', ''),
                                'timestamp': time.time(),
                                'source': 'plaza'
                            }
                            
                            listings.append(listing)
                            
                        except Exception as e:
                            print(f"Error processing Plaza listing: {e}")
                            continue
                    
                    print(f"Found {len(listings)} Plaza listings")
        
    except Exception as e:
        print(f"Error fetching Plaza listings: {e}")
    
    return listings

async def get_roomspot_listings():
    """Fetch listings from the Roomspot API."""
    listings = []
    
    try:
        print("🏠 Fetching Roomspot listings...")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                SCRAPERS['roomspot']['api_url'], 
                headers=HEADERS,
                json=ROOMSPOT_PAYLOAD
            ) as response:
                if response.status != 200:
                    print(f"Error: Roomspot API returned status code {response.status}")
                    return listings
                
                data = await response.json()
                
                if data and 'data' in data:
                    items = data['data']
                    print(f"Roomspot API returned {len(items)} items")
                    
                    for item in items:
                        try:
                            listing_id = str(item.get('id', ''))
                            
                            # Extract address components
                            street = item.get('street', '')
                            house_number = item.get('houseNumber', '')
                            house_number_addition = item.get('houseNumberAddition', '')
                            
                            city_name = item.get('gemeenteGeoLocatieNaam', '')
                            postal_code = item.get('postalcode', '')
                            
                            # Format the title
                            title_parts = [p for p in [street, house_number, house_number_addition] if p]
                            title = f"{' '.join(title_parts)}"
                            if postal_code or city_name:
                                title += f", {postal_code} {city_name}".strip()
                            
                            # Extract other details
                            price = ''
                            if item.get('totalRent'):
                                price = f"€{float(item['totalRent']):.2f}"
                            elif item.get('netRent'):
                                price = f"€{float(item['netRent']):.2f}"
                            else:
                                price = 'No price info'
                            
                            area = ''
                            if item.get('areaDwelling'):
                                area = f"{item['areaDwelling']} m²"
                            else:
                                area = 'No area info'
                            
                            property_type = ''
                            if isinstance(item.get('dwellingType'), dict):
                                property_type = item['dwellingType'].get('localizedName', '')
                            else:
                                property_type = item.get('objectType', '')
                            
                            house_type = ''
                            if isinstance(item.get('woningsoort'), dict):
                                house_type = item['woningsoort'].get('localizedNaam', '')
                            else:
                                house_type = item['toewijzingModelCategorie'].get('code', '')

                            # Extract image URL
                            img_url = ''
                            if item.get('pictures') and len(item['pictures']) > 0:
                                if isinstance(item['pictures'][0], dict) and 'url' in item['pictures'][0]:
                                    img_url = item['pictures'][0]['url']
                                elif isinstance(item['pictures'][0], dict) and 'uri' in item['pictures'][0]:
                                    img_url = item['pictures'][0]['uri']
                            
                            if img_url and not img_url.startswith(('http://', 'https://')):
                                img_url = f"https://www.roomspot.nl{img_url}"
                            
                            # Create link
                            components = [str(listing_id)]
                            
                            if street:
                                clean_street = street.lower().strip().replace(" ", "")
                                components.append(clean_street)
                            
                            if house_number:
                                components.append(str(house_number))
                            
                            if house_number_addition:
                                addition = str(house_number_addition).strip().replace(" ", "")
                                if addition:
                                    components.append(addition)
                            
                            if city_name:
                                clean_city = city_name.lower().strip().replace(" ", "")
                                components.append(clean_city)
                            
                            clean_url_path = "-".join(components)
                            link = f"https://www.roomspot.nl/en/housing-offer/to-rent/translate-to-engels-details/{clean_url_path}"
                            
                            if not title or title.isspace():
                                continue
                            
                            listing = {
                                'id': listing_id,
                                'title': title,
                                'price': price,
                                'area': area,
                                'property_type': property_type,
                                'house_type': house_type,
                                'link': link,
                                'img_url': img_url,
                                'publication_date': item.get('publicationDate', ''),
                                'timestamp': time.time(),
                                'source': 'roomspot'
                            }
                            
                            listings.append(listing)
                            
                        except Exception as e:
                            print(f"Error processing Roomspot listing: {e}")
                            continue
                    
                    print(f"Found {len(listings)} Roomspot listings")
        
    except Exception as e:
        print(f"Error fetching Roomspot listings: {e}")
    
    return listings

async def send_discord_notification(listing, webhook_url, source_config):
    """Send a notification to Discord about a new listing."""
    if not webhook_url:
        print(f"No webhook URL configured for {source_config['name']}")
        return
        
    try:
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(webhook_url, session=session)
            
            embed = discord.Embed(
                title=f"{source_config['emoji']} New {source_config['name']} Listing!",
                description=f"**{listing['title']}**",
                color=source_config['color'],
                url=listing['link']
            )
            
            # Add fields with details
            embed.add_field(name="Price", value=listing['price'], inline=True)
            embed.add_field(name="Area", value=listing['area'], inline=True)
            embed.add_field(name="Property Type", value=listing['property_type'], inline=True)
            
            if listing.get('floor'):
                embed.add_field(name="Floor", value=listing['floor'], inline=True)
            
            if listing.get('house_type'):
                embed.add_field(name="House Type", value=listing['house_type'], inline=True)
            
            # Add image if available
            if listing['img_url']:
                embed.set_image(url=listing['img_url'])
            
            # Add footer with timestamp and source
            embed.set_footer(
                text=f"{source_config['name']} • {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(listing['timestamp']))}"
            )
            
            await webhook.send(embed=embed)
            print(f"✅ Sent {source_config['name']} notification for: {listing['title']}")
    except Exception as e:
        print(f"❌ Error sending {source_config['name']} notification: {e}")

def load_seen_listings(filename):
    """Load previously seen listings from a JSON file."""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_seen_listings(listings, filename):
    """Save seen listings to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(listings, f)

async def process_scraper(scraper_name, scraper_config):
    """Process a single scraper."""
    if not scraper_config['webhook_url']:
        print(f"⚠️  Skipping {scraper_name} - no webhook URL configured")
        return
    
    print(f"\n🔍 Processing {scraper_config['name']} scraper...")
    
    # Load seen listings for this scraper
    seen_listings = load_seen_listings(scraper_config['seen_file'])
    
    # Get listings based on scraper type
    if scraper_name == 'plaza':
        current_listings = await get_plaza_listings()
    elif scraper_name == 'roomspot':
        current_listings = await get_roomspot_listings()
    else:
        print(f"Unknown scraper: {scraper_name}")
        return
    
    if not current_listings:
        print(f"No {scraper_config['name']} listings found")
        return
    
    # Check for new listings
    new_listings = []
    for listing in current_listings:
        if listing['id'] not in seen_listings:
            print(f"🆕 New {scraper_config['name']} listing: {listing['title']} (ID: {listing['id']})")
            new_listings.append(listing)
            seen_listings.append(listing['id'])
        else:
            print(f"👀 Known {scraper_config['name']} listing: {listing['title']}")
    
    print(f"📊 {scraper_config['name']}: {len(new_listings)} new listings out of {len(current_listings)} total")
    
    # Send notifications for new listings
    for listing in new_listings:
        await send_discord_notification(listing, scraper_config['webhook_url'], scraper_config)
    
    # Save updated seen listings
    save_seen_listings(seen_listings, scraper_config['seen_file'])

async def main():
    """Main function to run all scrapers."""
    print("🚀 Starting Combined Apartment Scraper...")
    print(f"📅 Check interval: {CHECK_INTERVAL} seconds")
    
    # Check which scrapers are enabled
    enabled_scrapers = []
    for name, config in SCRAPERS.items():
        if config['webhook_url']:
            enabled_scrapers.append(name)
            print(f"✅ {config['name']} scraper enabled")
        else:
            print(f"⚠️  {config['name']} scraper disabled (no webhook URL)")
    
    if not enabled_scrapers:
        print("❌ No scrapers enabled! Please configure webhook URLs in your .env file")
        return
    
    while True:
        try:
            print(f"\n{'='*50}")
            print(f"🔄 Starting scrape cycle at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*50}")
            
            # Process all enabled scrapers
            tasks = []
            for scraper_name in enabled_scrapers:
                tasks.append(process_scraper(scraper_name, SCRAPERS[scraper_name]))
            
            # Run all scrapers concurrently
            await asyncio.gather(*tasks)
            
            print(f"\n✅ Scrape cycle completed. Next check in {CHECK_INTERVAL} seconds...")
            await asyncio.sleep(CHECK_INTERVAL)
            
        except Exception as e:
            print(f"❌ Error in main loop: {e}")
            print("Traceback:", traceback.format_exc())
            await asyncio.sleep(60)  # Wait a minute before retrying

if __name__ == "__main__":
    asyncio.run(main()) 
