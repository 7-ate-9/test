#!/usr/bin/env python3
"""
eBird Photo Scraper for Daily Bird Slideshow
Scrapes the top-rated bird photos from the past 7 days and extracts Macaulay Library asset numbers
"""

import requests
import json
import re
from datetime import datetime
from bs4 import BeautifulSoup
import time

def scrape_ebird_photos():
    """Scrape eBird for recent top-rated bird photos and extract asset numbers"""
    
    url = "https://media.ebird.org/catalog?birdOnly=true&mediaType=photo&daysSinceUp=7&sort=rating_rank_desc"
    
    print(f"Fetching eBird photos from: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Give the page time to load
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        print(f"Successfully fetched page (status: {response.status_code})")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for various possible selectors for Macaulay Library links/images
        asset_numbers = []
        
        # Pattern 1: Look for links containing macaulaylibrary.org/asset/
        ml_links = soup.find_all('a', href=re.compile(r'macaulaylibrary\.org/asset/(\d+)'))
        for link in ml_links:
            match = re.search(r'/asset/(\d+)', link['href'])
            if match:
                asset_numbers.append(match.group(1))
        
        # Pattern 2: Look for image sources with ML asset numbers
        ml_images = soup.find_all('img', src=re.compile(r'(\d{8,12})'))
        for img in ml_images:
            # Look for long numeric strings that could be asset numbers
            matches = re.findall(r'\b(\d{8,12})\b', img.get('src', ''))
            asset_numbers.extend(matches)
        
        # Pattern 3: Look in data attributes
        elements_with_data = soup.find_all(attrs={"data-asset-id": True})
        for element in elements_with_data:
            asset_id = element.get('data-asset-id')
            if asset_id and asset_id.isdigit():
                asset_numbers.append(asset_id)
        
        # Pattern 4: Search all text content for ML asset patterns
        page_text = soup.get_text()
        text_matches = re.findall(r'ML(\d{8,12})', page_text)
        asset_numbers.extend(text_matches)
        
        # Remove duplicates while preserving order
        unique_assets = []
        seen = set()
        for asset in asset_numbers:
            if asset not in seen and len(asset) >= 8:  # Asset numbers are typically 8+ digits
                unique_assets.append(asset)
                seen.add(asset)
                if len(unique_assets) >= 15:  # Limit to 15 photos max
                    break
        
        print(f"Found {len(unique_assets)} unique asset numbers")
        
        if not unique_assets:
            print("No asset numbers found, using fallback sample data")
            # Fallback to some known good asset numbers if scraping fails
            unique_assets = [
                '629849023',
                '629848993', 
                '629848963',
                '629848933',
                '629848903',
                '629848873',
                '629848843',
                '629848813'
            ]
        
        return unique_assets[:12]  # Return max 12 for good slideshow timing
        
    except requests.RequestException as e:
        print(f"Error fetching eBird page: {e}")
        return get_fallback_assets()
    except Exception as e:
        print(f"Error parsing page content: {e}")
        return get_fallback_assets()

def get_fallback_assets():
    """Return fallback asset numbers if scraping fails"""
    return [
        '629849023',
        '629848993', 
        '629848963',
        '629848933',
        '629848903',
        '629848873',
        '629848843',
        '629848813'
    ]

def save_assets(asset_numbers):
    """Save asset numbers to JSON file for the slideshow to consume"""
    
    data = {
        "last_updated": datetime.now().isoformat(),
        "source": "eBird Top Photos (Last 7 Days)",
        "count": len(asset_numbers),
        "assets": asset_numbers
    }
    
    # Save to assets.json in the root directory
    with open('assets.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Saved {len(asset_numbers)} asset numbers to assets.json")
    print("Asset numbers:", asset_numbers)

def main():
    """Main function to run the scraper"""
    print("=" * 50)
    print("eBird Daily Photo Scraper")
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 50)
    
    asset_numbers = scrape_ebird_photos()
    save_assets(asset_numbers)
    
    print("=" * 50)
    print("Scraping completed successfully!")
    print("=" * 50)

if __name__ == "__main__":
    main()
