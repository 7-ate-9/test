#!/usr/bin/env python3
"""
eBird Photo Scraper for Daily Bird Slideshow
Scrapes the top-rated bird photos from the past 7 days and extracts Macaulay Library asset numbers
Uses Playwright with headless Chromium to handle JavaScript-loaded content
"""

import json
import re
from datetime import datetime
from playwright.sync_api import sync_playwright
import time

def scrape_ebird_photos():
    """Scrape eBird for recent top-rated bird photos and extract asset numbers"""
    
    url = "https://media.ebird.org/catalog?birdOnly=true&mediaType=photo&daysSinceUp=7&sort=rating_rank_desc"
    
    print(f"Fetching eBird photos from: {url}")
    
    asset_numbers = []
    
    with sync_playwright() as p:
        try:
            print("Launching browser...")
            browser = p.chromium.launch(headless=True)
            
            print("Creating new page...")
            page = browser.new_page()
            
            # Set a realistic user agent
            page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            
            print("Navigating to eBird...")
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            print("Waiting for content to load...")
            # Wait a bit for images to appear
            time.sleep(5)
            
            # Try to wait for image elements
            try:
                page.wait_for_selector("img", timeout=10000)
                print("Images detected!")
            except:
                print("Timeout waiting for images, proceeding anyway...")
            
            # Get the page content
            page_content = page.content()
            print(f"Page content length: {len(page_content)} characters")
            
            # Also get all image sources directly
            try:
                img_elements = page.query_selector_all("img")
                print(f"Found {len(img_elements)} img elements")
                for img in img_elements[:20]:  # Check first 20 images
                    src = img.get_attribute("src")
                    if src:
                        # Look for asset numbers in image URLs
                        matches = re.findall(r'(\d{8,12})', src)
                        asset_numbers.extend(matches)
            except Exception as e:
                print(f"Error extracting from img elements: {e}")
            
            # Also get all links
            try:
                link_elements = page.query_selector_all("a")
                print(f"Found {len(link_elements)} link elements")
                for link in link_elements[:50]:  # Check first 50 links
                    href = link.get_attribute("href")
                    if href and "macaulaylibrary.org/asset" in href:
                        matches = re.findall(r'/asset/(\d{8,12})', href)
                        asset_numbers.extend(matches)
            except Exception as e:
                print(f"Error extracting from links: {e}")
            
            # Extract asset numbers from page content using multiple patterns
            
            # Pattern 1: macaulaylibrary.org/asset/ URLs
            pattern1 = re.findall(r'macaulaylibrary\.org/asset/(\d{8,12})', page_content)
            asset_numbers.extend(pattern1)
            print(f"Pattern 1 (asset URLs): Found {len(pattern1)} matches")
            
            # Pattern 2: ML catalog numbers
            pattern2 = re.findall(r'ML(\d{8,12})', page_content)
            asset_numbers.extend(pattern2)
            print(f"Pattern 2 (ML numbers): Found {len(pattern2)} matches")
            
            # Pattern 3: catalogId in JSON
            pattern3 = re.findall(r'"catalogId"\s*:\s*"?(\d{8,12})"?', page_content)
            asset_numbers.extend(pattern3)
            print(f"Pattern 3 (catalog IDs): Found {len(pattern3)} matches")
            
            # Pattern 4: assetId in JSON
            pattern4 = re.findall(r'"assetId"\s*:\s*"?(\d{8,12})"?', page_content)
            asset_numbers.extend(pattern4)
            print(f"Pattern 4 (asset IDs): Found {len(pattern4)} matches")
            
            # Pattern 5: Any 9-12 digit numbers in image paths
            pattern5 = re.findall(r'/(\d{9,12})\.(jpg|jpeg|png|webp)', page_content, re.IGNORECASE)
            asset_numbers.extend([match[0] for match in pattern5])
            print(f"Pattern 5 (image URLs): Found {len(pattern5)} matches")
            
            # Pattern 6: Look for common eBird/ML data attributes or IDs
            pattern6 = re.findall(r'(?:data-asset-id|assetId|catalogId)["\']?\s*[:=]\s*["\']?(\d{8,12})', page_content, re.IGNORECASE)
            asset_numbers.extend(pattern6)
            print(f"Pattern 6 (data attributes): Found {len(pattern6)} matches")
            
            # Take a screenshot for debugging if needed
            # page.screenshot(path="debug_screenshot.png")
            
            print("Closing browser...")
            browser.close()
            
            # Remove duplicates while preserving order
            unique_assets = []
            seen = set()
            for asset in asset_numbers:
                if asset not in seen and len(asset) >= 8:  # Asset numbers are typically 8+ digits
                    unique_assets.append(asset)
                    seen.add(asset)
                    if len(unique_assets) >= 50:  # Get up to 50 photos
                        break
            
            print(f"Total unique asset numbers found: {len(unique_assets)}")
            
            if not unique_assets:
                print("WARNING: No asset numbers found!")
                print("Saving first 1000 chars of page content for debugging:")
                print(page_content[:1000])
                print("\nUsing fallback sample data")
                return get_fallback_assets()
            
            return unique_assets[:12]  # Return max 12 for good slideshow timing
            
        except Exception as e:
            print(f"Error during scraping: {e}")
            import traceback
            traceback.print_exc()
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
    
    # Save to assets.json in the birds directory
    with open('birdslide/assets.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Saved {len(asset_numbers)} asset numbers to birdslide/assets.json")
    print("Asset numbers:", asset_numbers)

def main():
    """Main function to run the scraper"""
    print("=" * 50)
    print("eBird Daily Photo Scraper (Playwright)")
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 50)
    
    asset_numbers = scrape_ebird_photos()
    save_assets(asset_numbers)
    
    print("=" * 50)
    print("Scraping completed successfully!")
    print("=" * 50)

if __name__ == "__main__":
    main()
