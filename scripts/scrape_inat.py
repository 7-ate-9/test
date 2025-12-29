#!/usr/bin/env python3
"""
iNaturalist Observation Scraper
Fetches observations with photos using the iNaturalist API
"""

import requests
import json
from datetime import datetime
import sys
import time

def scrape_inat_observations(taxon_id='', quality_grade='', per_page=30, **kwargs):
    """
    Scrape iNaturalist for observations with photos
    
    Args:
        taxon_id: Taxon ID (e.g., '551307' for sharks)
        quality_grade: 'research' or 'needs_id' or leave empty for both
        per_page: Number of results (max 200)
        **kwargs: Additional API parameters (term_id, term_value_id, etc.)
    """
    
    base_url = "https://api.inaturalist.org/v1/observations"
    
    # Build parameters
    params = {
        'per_page': min(per_page, 200),  # API max is 200
        'order': 'desc',
        'order_by': 'created_at',
        'photos': 'true',  # Only observations with photos
        'photo_licensed': 'true',  # Only Creative Commons licensed photos
        'captive': 'false',  # Exclude captive/cultivated organisms
        'verifiable': 'true',  # Only verifiable observations (research grade + needs ID)
    }
    
    if taxon_id:
        params['taxon_id'] = taxon_id
    
    if quality_grade:
        params['quality_grade'] = quality_grade
    
    # Add any additional parameters from kwargs
    params.update(kwargs)
    
    print("=" * 50)
    print("iNaturalist Observation Scraper")
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 50)
    print(f"\nFetching observations from iNaturalist API...")
    print(f"Full API URL parameters:")
    for key, value in params.items():
        print(f"  {key}: {value}")
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        results = data.get('results', [])
        total_results = data.get('total_results', 0)
        
        print(f"API returned {len(results)} observations (out of {total_results} total)")
        
        observations = []
        
        for obs in results:
            # Get first photo only
            photos = obs.get('photos', [])
            if not photos:
                continue
            
            photo = photos[0]
            
            # Get taxon info
            taxon = obs.get('taxon', {})
            common_name = taxon.get('preferred_common_name', '')
            scientific_name = taxon.get('name', 'Unknown species')
            
            # Get observer info
            user = obs.get('user', {})
            observer_login = user.get('login', 'Unknown')
            observer_name = user.get('name', observer_login)
            
            # Get location info
            place_guess = obs.get('place_guess', '')
            location = place_guess if place_guess else 'Location obscured'
            
            # Get date
            observed_on = obs.get('observed_on_string', obs.get('created_at', ''))
            
            # Get license info
            license_code = photo.get('license_code')
            if not license_code:
                # Skip if no license (shouldn't happen with photo_licensed=true, but be safe)
                continue
            
            license_name = get_license_name(license_code)
            license_url = get_license_url(license_code)
            
            # Get image URL (large size)
            image_url = photo.get('url', '').replace('square', 'large')
            
            # Build observation object
            observation = {
                'id': obs.get('id'),
                'image_url': image_url,
                'species_common': common_name,
                'species_scientific': scientific_name,
                'observer': observer_name,
                'observer_login': observer_login,
                'date': observed_on,
                'location': location,
                'license_code': license_code,
                'license_name': license_name,
                'license_url': license_url,
                'obs_url': f"https://www.inaturalist.org/observations/{obs.get('id')}",
                'quality_grade': obs.get('quality_grade', '')
            }
            
            observations.append(observation)
            
            if len(observations) >= per_page:
                break
        
        print(f"Successfully processed {len(observations)} observations with licensed photos")
        return observations
        
    except requests.RequestException as e:
        print(f"Error fetching from iNaturalist API: {e}")
        return get_fallback_observations()
    except Exception as e:
        print(f"Error processing observations: {e}")
        import traceback
        traceback.print_exc()
        return get_fallback_observations()

def get_license_name(license_code):
    """Convert license code to readable name"""
    licenses = {
        'cc-by': 'CC BY',
        'cc-by-nc': 'CC BY-NC',
        'cc-by-sa': 'CC BY-SA',
        'cc-by-nd': 'CC BY-ND',
        'cc-by-nc-sa': 'CC BY-NC-SA',
        'cc-by-nc-nd': 'CC BY-NC-ND',
        'cc0': 'CC0 (Public Domain)'
    }
    return licenses.get(license_code.lower(), license_code.upper())

def get_license_url(license_code):
    """Get URL for license deed"""
    base = "https://creativecommons.org/licenses/"
    
    if license_code.lower() == 'cc0':
        return "https://creativecommons.org/publicdomain/zero/1.0/"
    
    # Extract license type (e.g., 'by-nc' from 'cc-by-nc')
    license_type = license_code.lower().replace('cc-', '')
    return f"{base}{license_type}/4.0/"

def get_fallback_observations():
    """Return fallback observations if API fails"""
    return [
        {
            'id': 123456789,
            'image_url': 'https://via.placeholder.com/1024x768?text=iNaturalist+observation',
            'species_common': 'Sample Species',
            'species_scientific': 'Genus species',
            'observer': 'Sample Observer',
            'observer_login': 'observer',
            'date': 'Dec 15, 2025',
            'location': 'Sample Location',
            'license_code': 'cc-by',
            'license_name': 'CC BY',
            'license_url': 'https://creativecommons.org/licenses/by/4.0/',
            'obs_url': 'https://www.inaturalist.org',
            'quality_grade': 'research'
        }
    ]

def save_observations(observations, taxon_id=''):
    """Save observations to JSON file for the slideshow to consume"""
    
    data = {
        "last_updated": datetime.now().isoformat(),
        "source": "iNaturalist",
        "taxon_id": taxon_id,
        "count": len(observations),
        "observations": observations
    }
    
    # Save to observations.json in the birds directory (reusing same directory)
    with open('inatslide/observations.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\nSaved {len(observations)} observations to inatslide/observations.json")
    print(f"First observation: {observations[0]['species_scientific'] if observations else 'None'}")

def main():
    """Main function to run the scraper"""
    
    # Parse command line arguments
    taxon_id = ''
    quality_grade = ''
    per_page = 30
    additional_params = {}
    
    for arg in sys.argv[1:]:
        if arg.startswith('--taxon='):
            taxon_id = arg.split('=', 1)[1]
            print(f"Taxon ID: {taxon_id}")
        elif arg.startswith('--quality='):
            quality_grade = arg.split('=', 1)[1]
            print(f"Quality grade filter: {quality_grade}")
        elif arg.startswith('--count='):
            per_page = int(arg.split('=', 1)[1])
            print(f"Number of observations: {per_page}")
        elif arg.startswith('--'):
            # Handle additional API parameters like --term_id=17
            key, value = arg[2:].split('=', 1)
            additional_params[key] = value
            print(f"Additional parameter: {key}={value}")
    
    observations = scrape_inat_observations(
        taxon_id=taxon_id,
        quality_grade=quality_grade,
        per_page=per_page,
        **additional_params
    )
    
    save_observations(observations, taxon_id)
    
    print("=" * 50)
    print("Scraping completed successfully!")
    print("=" * 50)

if __name__ == "__main__":
    main()
