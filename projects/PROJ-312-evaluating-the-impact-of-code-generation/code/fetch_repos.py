"""
Module to fetch repository metadata from the GitHub API.
Implements T012a: Fetch top Python and JavaScript repositories by star count.
"""
import json
import logging
import os
import time
from pathlib import Path
from typing import List, Dict, Any

import requests

from utils import api_request_with_backoff, log_api_headers

# Configuration
GITHUB_API_BASE = "https://api.github.com"
PYTHON_QUERY = "language:Python+stars:>10000&sort=stars&order=desc"
JS_QUERY = "language:JavaScript+stars:>10000&sort=stars&order=desc"
OUTPUT_PATH = Path("data/raw/repos.json")
REPO_LIMIT = 100  # Fetch up to 100 repos per language to ensure a representative set

def setup_logging():
    """Configure logging for the fetch_repos module."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/pipeline.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def fetch_repos_from_github(query: str, language_name: str, logger: logging.Logger) -> List[Dict[str, Any]]:
    """
    Fetch repositories from GitHub API based on a search query.
    
    Args:
        query: The search query string (e.g., 'language:Python+stars:>10000...')
        language_name: Human-readable name for logging (e.g., 'Python')
        logger: Logger instance
        
    Returns:
        List of repository dictionaries containing 'name' and 'stars'.
    """
    url = f"{GITHUB_API_BASE}/search/repositories"
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": 100
    }
    
    headers = {}
    # Check for optional GitHub token
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    
    repos = []
    page = 1
    total_fetched = 0
    
    logger.info(f"Fetching {language_name} repositories...")
    
    while total_fetched < REPO_LIMIT:
        params["page"] = page
        try:
            response = api_request_with_backoff(url, headers, params=params)
            log_api_headers(response)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch page {page}: HTTP {response.status_code}")
                break
            
            data = response.json()
            items = data.get("items", [])
            
            if not items:
                logger.info("No more items found.")
                break
            
            # Process items
            for item in items:
                if total_fetched >= REPO_LIMIT:
                    break
                repos.append({
                    "name": item["full_name"],
                    "stars": item["stargazers_count"]
                })
                total_fetched += 1
            
            logger.info(f"Fetched page {page}, total repos so far: {total_fetched}")
            page += 1
            
        except Exception as e:
            logger.error(f"Error fetching page {page}: {str(e)}")
            break
    
    logger.info(f"Successfully fetched {len(repos)} {language_name} repositories.")
    return repos

def main():
    """Main entry point for fetching repository data."""
    logger = setup_logging()
    logger.info("Starting repository fetch for T012a.")
    
    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    all_repos = []
    
    # Fetch Python repos
    python_repos = fetch_repos_from_github(PYTHON_QUERY, "Python", logger)
    all_repos.extend(python_repos)
    
    # Fetch JavaScript repos
    js_repos = fetch_repos_from_github(JS_QUERY, "JavaScript", logger)
    all_repos.extend(js_repos)
    
    # Save to JSON
    try:
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(all_repos, f, indent=2)
        logger.info(f"Saved {len(all_repos)} repositories to {OUTPUT_PATH}")
    except IOError as e:
        logger.error(f"Failed to write output file: {e}")
        raise

if __name__ == "__main__":
    main()
