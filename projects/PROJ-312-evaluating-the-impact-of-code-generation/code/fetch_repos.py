import json
import logging
import os
import time
from pathlib import Path
from typing import List, Dict, Any

import requests

from utils import api_request_with_backoff, log_api_headers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"

def fetch_repos_from_github(language: str, min_stars: int = 10000, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Fetch top repositories for a given language sorted by stars.
    
    Args:
        language: Language to search for (e.g., 'Python', 'JavaScript')
        min_stars: Minimum star count filter
        limit: Maximum number of repos to fetch
        
    Returns:
        List of repository dictionaries containing 'name' and 'stars'
    """
    repos = []
    query = f"language:{language}+stars:>{min_stars}"
    url = f"{GITHUB_API_BASE}/search/repositories"
    params = {
        'q': query,
        'sort': 'stars',
        'order': 'desc',
        'per_page': 100
    }
    
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'llmXive-Research-Pipeline'
    }
    
    logger.info(f"Fetching top {limit} {language} repositories with >{min_stars} stars...")
    
    page = 1
    while len(repos) < limit:
        params['page'] = page
        try:
            response = api_request_with_backoff(url, headers, params=params)
            log_api_headers(response)
            
            if response.status_code != 200:
                logger.error(f"API request failed with status {response.status_code}")
                raise RuntimeError(f"GitHub API request failed: {response.status_code} {response.text}")
            
            data = response.json()
            items = data.get('items', [])
            
            if not items:
                logger.warning(f"No more items found for page {page}")
                break
            
            for repo in items:
                if len(repos) >= limit:
                    break
                
                repo_info = {
                    'name': repo['full_name'],
                    'stars': repo['stargazers_count'],
                    'language': repo.get('language', language)
                }
                repos.append(repo_info)
            
            logger.info(f"Page {page}: fetched {len(items)} items, total repos: {len(repos)}")
            page += 1
            time.sleep(1)  # Respect rate limits between pages
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching page {page}: {e}")
            raise
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            raise

    logger.info(f"Successfully fetched {len(repos)} repositories for {language}")
    return repos

def main():
    """Main entry point for fetching repository data."""
    output_dir = Path('data/raw')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / 'repos.json'
    
    # Fetch top Python repos
    python_repos = fetch_repos_from_github('Python', min_stars=10000, limit=50)
    
    # Fetch top JavaScript repos
    js_repos = fetch_repos_from_github('JavaScript', min_stars=10000, limit=50)
    
    # Combine results
    all_repos = python_repos + js_repos
    
    logger.info(f"Total repositories collected: {len(all_repos)}")
    
    # Save to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_repos, f, indent=2)
    
    logger.info(f"Repository data saved to {output_file}")
    print(f"Successfully saved {len(all_repos)} repositories to {output_file}")

if __name__ == '__main__':
    main()
