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

# Load environment variables
load_dotenv()

# Constants
API_URL = "https://mosaic-plaza-aanbodapi.zig365.nl/api/v1/actueel-aanbod?limit=60&locale=en_GB&page=0&sort=%2BreactionData.aangepasteTotaleHuurprijs"
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
CHECK_INTERVAL = 300  # 5 minutes

# Filters payload for Enschede (municipality.id: 15897)
API_PAYLOAD = {
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

# Headers to mimic a browser request
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://plaza.newnewnew.space/en/availables-places/living-place',
    'Origin': 'https://plaza.newnewnew.space',
    'Content-Type': 'application/json'
}

async def get_listings(debug=False):
    """Fetch listings from the API with the Enschede filters."""
    listings = []
    
    try:
        print("Fetching listings from API...")
        async with aiohttp.ClientSession() as session:
            # Make a POST request with the filters payload
            async with session.post(
                API_URL, 
                headers=HEADERS,
                json=API_PAYLOAD
            ) as response:
                if response.status != 200:
                    print(f"Error: API returned status code {response.status}")
                    return listings
                
                data = await response.json()
                
                print(f"API response keys: {data.keys() if data else 'None'}")
                
                # Check if the response has the structure with 'data' key
                if data and 'data' in data:
                    items = data['data']
                    print(f"API returned {len(items)} items")
                    
                    # Dump a sample item for debugging if available
                    if items and debug:
                        try:
                            sample_item = items[0]
                            print(f"Sample item keys: {sample_item.keys()}")
                            print(f"Sample street: {sample_item.get('street')}")
                            print(f"Sample houseNumber: {sample_item.get('houseNumber')}")
                            print(f"Sample city: {sample_item.get('city', {}).get('name', '')}")
                            print(f"Sample postalcode: {sample_item.get('postalcode')}")
                            print(f"Sample totalRent: {sample_item.get('totalRent')}")
                            print(f"Sample areaDwelling: {sample_item.get('areaDwelling')}")
                        except Exception as e:
                            print(f"Error printing sample item: {e}")
                    
                    # Process each listing
                    for item in items:
                        try:
                            # Extract listing details
                            listing_id = str(item.get('id', ''))
                            
                            # Extract address components directly from API response
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
                            
                            # Extract price
                            price = ''
                            if item.get('totalRent'):
                                price = f"€{float(item['totalRent']):.2f}"
                            elif item.get('netRent'):
                                price = f"€{float(item['netRent']):.2f}"
                            else:
                                price = 'No price info'
                            
                            # Extract area
                            area = ''
                            if item.get('areaDwelling'):
                                area = f"{item['areaDwelling']} m²"
                            else:
                                area = 'No area info'
                            
                            # Extract property type
                            property_type = ''
                            if isinstance(item.get('dwellingType'), dict):
                                property_type = item['dwellingType'].get('name', '')
                            else:
                                property_type = item.get('objectType', '')
                            
                            # Extract floor
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
                            
                            # Ensure img_url is a complete URL
                            if img_url and not img_url.startswith(('http://', 'https://')):
                                img_url = f"https://plaza.newnewnew.space{img_url}"
                            
                            # Extract publication date
                            publication_date = item.get('publicationDate', '')
                            
                            # Create link using the id and a URL friendly version of the title
                            cleaned_title = re.sub(r'[^a-z0-9]', '-', title.lower())
                            cleaned_title = re.sub(r'-+', '-', cleaned_title).strip('-')
                            
                            link = f"https://plaza.newnewnew.space/en/availables-places/living-place/details/{listing_id}"
                            if cleaned_title:
                                link += f"-{cleaned_title}"
                            
                            # Only include listings with a valid title
                            if not title or title.isspace():
                                print(f"Skipping listing {listing_id} with empty title")
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
                                'publication_date': publication_date,
                                'timestamp': time.time()
                            }
                            
                            listings.append(listing)
                            
                        except Exception as e:
                            print(f"Error processing listing: {e}")
                            continue
                    
                    print(f"Found {len(listings)} Enschede listings")
                else:
                    print("Error: API response doesn't have expected 'data' key")
        
    except Exception as e:
        print(f"Error fetching listings from API: {e}")
    
    return listings

async def send_discord_notification(listing):
    """Send a notification to Discord about a new listing."""
    try:
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(DISCORD_WEBHOOK_URL, session=session)
            
            embed = discord.Embed(
                title="New Apartment Listing! 🏠",
                description=f"**{listing['title']}**",
                color=discord.Color.green(),
                url=listing['link']
            )
            
            # Add fields with details
            embed.add_field(name="Price", value=listing['price'], inline=True)
            embed.add_field(name="Area", value=listing['area'], inline=True)
            
            
            if listing.get('floor'):
                embed.add_field(name="Floor", value=listing['floor'], inline=True)
            

            # Add image if available
            if listing['img_url']:
                embed.set_image(url=listing['img_url'])
            
            # Add footer with timestamp
            embed.set_footer(text=f"Found on {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(listing['timestamp']))}")
            
            await webhook.send(embed=embed)
            print(f"Sent notification for: {listing['title']}")
    except Exception as e:
        print(f"Error sending Discord notification: {e}")

def load_seen_listings():
    """Load previously seen listings from a JSON file."""
    try:
        with open('seen_listings.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_seen_listings(listings):
    """Save seen listings to a JSON file."""
    with open('seen_listings.json', 'w') as f:
        json.dump(listings, f)

async def main():
    """Main function to run the scraper."""
    print("Starting Plaza apartment scraper...")
    seen_listings = load_seen_listings()
    print(f"Loaded {len(seen_listings)} previously seen listings")
    
    # First run - use debug mode
    first_run = True
    
    while True:
        try:
            print("Fetching current listings...")
            current_listings = await get_listings(debug=first_run)
            print(f"Found {len(current_listings)} listings in total")
            
            if not current_listings:
                print("No listings were found. Retrying in 60 seconds...")
                await asyncio.sleep(60)
                continue
            
            # Check for new listings
            new_listings = []
            for listing in current_listings:
                if listing['id'] not in seen_listings:
                    print(f"New listing found: {listing['title']} (ID: {listing['id']})")
                    new_listings.append(listing)
                    seen_listings.append(listing['id'])
                else:
                    print(f"Known listing: {listing['title']} (ID: {listing['id']})")
            
            print(f"Found {len(new_listings)} new listings")
            
            # Send notifications for new listings
            for listing in new_listings:
                print(f"Sending notification for: {listing['title']}")
                await send_discord_notification(listing)
            
            # Save updated seen listings
            save_seen_listings(seen_listings)
            
            # Wait longer on first run
            if first_run:
                print("First run completed with debugging.")
                print(f"Next check in {CHECK_INTERVAL} seconds...")
                first_run = False
            else:
                print(f"Checked listings. Waiting {CHECK_INTERVAL} seconds before next check...")
            
            await asyncio.sleep(CHECK_INTERVAL)
            
        except Exception as e:
            print(f"Error in main loop: {e}")
            print("Traceback:", traceback.format_exc())
            await asyncio.sleep(60)  # Wait a minute before retrying

if __name__ == "__main__":
    asyncio.run(main()) 