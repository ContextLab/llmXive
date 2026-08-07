"""
code/data/external.py

Fetches external metrics (GitHub stars, NPM downloads) for tags mapped in trend results.
Implements FR-007: External Validation.
"""

import os
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_TAXONOMY_DIR = PROJECT_ROOT / "data" / "taxonomy"

# Ensure output directories exist
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
DATA_TAXONOMY_DIR.mkdir(parents=True, exist_ok=True)

# API Configuration
GITHUB_API_URL = "https://api.github.com/search/repositories"
NPM_API_URL = "https://registry.npmjs.org/-/v1/search"
REQUEST_TIMEOUT = 10
RATE_LIMIT_SLEEP = 1.0  # Seconds to sleep between requests to respect rate limits

def load_trend_results() -> List[Dict[str, Any]]:
    """
    Loads the processed trend results from data/processed/trend_results.json.
    Returns a list of tag data dictionaries.
    """
    trend_file = DATA_PROCESSED_DIR / "trend_results.json"
    if not trend_file.exists():
        raise FileNotFoundError(
            f"Upstream artifact not found: {trend_file}. "
            "Ensure T014/T018 (trend analysis) has completed successfully."
        )
    
    with open(trend_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle structure if it's a dict with a 'tags' key or a list directly
    if isinstance(data, dict) and 'tags' in data:
        return data['tags']
    elif isinstance(data, list):
        return data
    else:
        raise ValueError(f"Unexpected format in {trend_file}")

def fetch_github_stars(tag_name: str, max_retries: int = 3) -> Optional[Dict[str, Any]]:
    """
    Fetches GitHub repository stars for a given tag using the Search API.
    Maps tag to a likely repository (e.g., 'react' -> 'facebook/react').
    Returns None if no match found or API fails.
    
    Strategy:
    1. Search for repos with topic:tag_name.
    2. If multiple, pick the one with the most stars.
    3. Return star count and repo details.
    """
    query = f"topic:{tag_name} in:readme"
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": 10
    }

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "llmXive-Research-Agent"
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(GITHUB_API_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                
                if not items:
                    return None
                
                # Take the top result (most stars)
                top_repo = items[0]
                return {
                    "source": "github",
                    "tag": tag_name,
                    "matched_repo": top_repo.get("full_name"),
                    "stars": top_repo.get("stargazers_count"),
                    "url": top_repo.get("html_url"),
                    "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                }
            elif response.status_code == 403:
                # Rate limited
                if 'Retry-After' in response.headers:
                    sleep_time = int(response.headers['Retry-After'])
                else:
                    sleep_time = 60
                print(f"GitHub Rate limited. Sleeping for {sleep_time}s.")
                time.sleep(sleep_time)
                continue
            else:
                print(f"GitHub API Error for {tag_name}: {response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Network error fetching GitHub for {tag_name}: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                return None

    return None

def fetch_npm_downloads(tag_name: str, max_retries: int = 3) -> Optional[Dict[str, Any]]:
    """
    Fetches NPM download counts for a given tag.
    Maps tag to a likely package name (e.g., 'react' -> 'react').
    Returns None if no match found or API fails.
    
    Strategy:
    1. Search NPM registry for keyword:tag_name.
    2. If found, get the top package.
    3. Fetch weekly downloads for that package.
    """
    # Step 1: Search for the package
    search_params = {
        "text": f"keywords:{tag_name}",
        "size": 10
    }

    try:
        search_response = requests.get(NPM_API_URL, params=search_params, timeout=REQUEST_TIMEOUT)
        if search_response.status_code != 200:
            return None
        
        search_data = search_response.json()
        objects = search_data.get('objects', [])
        
        if not objects:
            return None

        # Take the top result
        top_obj = objects[0]
        package_name = top_obj.get('package', {}).get('name')
        
        if not package_name:
            return None

        # Step 2: Fetch weekly downloads
        downloads_url = f"https://api.npmjs.org/downloads/point/last-week/{package_name}"
        downloads_response = requests.get(downloads_url, timeout=REQUEST_TIMEOUT)
        
        if downloads_response.status_code == 200:
            downloads_data = downloads_response.json()
            count = downloads_data.get('downloads')
            return {
                "source": "npm",
                "tag": tag_name,
                "matched_package": package_name,
                "weekly_downloads": count,
                "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
        elif downloads_response.status_code == 404:
            # Package exists but no download stats or not found
            return None
        else:
            print(f"NPM API Error for {package_name}: {downloads_response.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Network error fetching NPM for {tag_name}: {e}")
        return None

def fetch_external_metrics() -> Dict[str, Any]:
    """
    Orchestrates the fetching of external metrics for all tags in trend_results.
    Writes raw metrics to data/processed/external_metrics.json.
    Logs unmapped tags to data/processed/unmapped_tags.log.
    """
    print("Loading trend results...")
    tags_data = load_trend_results()
    
    if not tags_data:
        print("No tags found in trend results. Exiting.")
        return {"tags": [], "unmapped": []}

    results = []
    unmapped_tags = []

    print(f"Processing {len(tags_data)} tags for external metrics...")
    
    for item in tags_data:
        tag_name = item.get('tag') or item.get('name')
        if not tag_name:
            continue

        tag_name_lower = str(tag_name).strip().lower()
        
        print(f"  Fetching metrics for: {tag_name_lower}")
        
        github_data = None
        npm_data = None

        # Fetch GitHub
        github_data = fetch_github_stars(tag_name_lower)
        
        # Small delay to be polite to APIs
        time.sleep(RATE_LIMIT_SLEEP)

        # Fetch NPM
        npm_data = fetch_npm_downloads(tag_name_lower)
        
        time.sleep(RATE_LIMIT_SLEEP)

        combined_entry = {
            "tag": tag_name_lower,
            "github": github_data,
            "npm": npm_data
        }

        if github_data is None and npm_data is None:
            unmapped_tags.append(tag_name_lower)
        
        results.append(combined_entry)

    # Prepare output structure
    output_data = {
        "tags": results,
        "summary": {
            "total_processed": len(results),
            "total_unmapped": len(unmapped_tags)
        }
    }

    # Write main output file
    output_file = DATA_PROCESSED_DIR / "external_metrics.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"External metrics written to: {output_file}")

    # Write unmapped log
    unmapped_file = DATA_PROCESSED_DIR / "unmapped_tags.log"
    with open(unmapped_file, 'w', encoding='utf-8') as f:
        for tag in unmapped_tags:
            f.write(f"{tag}\n")
    
    if unmapped_tags:
        print(f"Unmapped tags written to: {unmapped_file} ({len(unmapped_tags)} tags)")
    else:
        print("All tags successfully mapped.")

    return output_data

def save_external_metrics(data: Dict[str, Any]) -> Path:
    """
    Saves the external metrics data to disk.
    (Helper function, primarily used if data is pre-fetched).
    """
    output_file = DATA_PROCESSED_DIR / "external_metrics.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    return output_file

def main():
    """
    Main entry point for fetching external metrics.
    """
    print("Starting External Metrics Fetcher (T039)...")
    try:
        fetch_external_metrics()
        print("External Metrics Fetcher completed successfully.")
    except FileNotFoundError as e:
        print(f"Critical Error: {e}")
        print("Please ensure T018 (trend_results.json generation) is completed first.")
        raise
    except Exception as e:
        print(f"Unexpected error during execution: {e}")
        raise

if __name__ == "__main__":
    main()