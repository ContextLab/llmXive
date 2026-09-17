"""
Fetch top Python and JavaScript repositories from GitHub API.

This module implements T012a: Fetch a representative set of top Python and JavaScript
repositories by star count using GitHub API endpoints and save the output to data/raw/repos.json.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import List, Dict, Any

# Import utilities from sibling module
from utils import api_request_with_backoff

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# GitHub API configuration
GITHUB_API_BASE = "https://api.github.com"
RATE_LIMIT_DELAY = 1.0  # Base delay to respect rate limits

def fetch_repos_from_github(language: str, min_stars: int = 10000, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Fetch top repositories for a given language from GitHub API.
    
    Args:
        language: Programming language (e.g., 'Python', 'JavaScript')
        min_stars: Minimum star count threshold
        limit: Maximum number of repositories to fetch
    
    Returns:
        List of repository dictionaries with 'name' and 'stars' keys
    
    Raises:
        RuntimeError: If API request fails after retries
    """
    # Construct query: language:Python+stars:>10000&sort=stars&order=desc
    query = f"language:{language}+stars:>{min_stars}&sort=stars&order=desc"
    url = f"{GITHUB_API_BASE}/search/repositories?q={query}&per_page={limit}"
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "llmXive-Research-Agent"
    }
    
    logger.info(f"Fetching {language} repositories from GitHub API: {url}")
    
    # Use the backoff utility for rate limit handling
    response = api_request_with_backoff(url, headers)
    
    if not response or response.status_code != 200:
        error_msg = f"Failed to fetch {language} repositories. Status code: {response.status_code if response else 'No response'}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    try:
        data = response.json()
        items = data.get('items', [])
        
        logger.info(f"Retrieved {len(items)} repositories for {language}")
        
        # Extract only 'name' and 'stars' as required by FR-001
        repos = []
        for item in items:
            repos.append({
                "name": item['full_name'],
                "stars": item['stargazers_count']
            })
        
        return repos
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response for {language}: {e}")
        raise RuntimeError(f"JSON parsing failed: {e}")
    except KeyError as e:
        logger.error(f"Missing expected key in response for {language}: {e}")
        raise RuntimeError(f"Missing key in response: {e}")

def main():
    """
    Main entry point for T012a.
    
    Fetches top Python and JavaScript repositories and saves them to data/raw/repos.json.
    """
    # Ensure output directory exists
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "repos.json"
    
    logger.info(f"Starting repository fetch. Output will be saved to: {output_file}")
    
    all_repos = []
    
    # Fetch Python repositories
    try:
        python_repos = fetch_repos_from_github("Python", min_stars=10000, limit=50)
        all_repos.extend(python_repos)
        logger.info(f"Successfully fetched {len(python_repos)} Python repositories")
    except Exception as e:
        logger.error(f"Failed to fetch Python repositories: {e}")
        raise
    
    # Fetch JavaScript repositories
    try:
        js_repos = fetch_repos_from_github("JavaScript", min_stars=10000, limit=50)
        all_repos.extend(js_repos)
        logger.info(f"Successfully fetched {len(js_repos)} JavaScript repositories")
    except Exception as e:
        logger.error(f"Failed to fetch JavaScript repositories: {e}")
        raise
    
    # Validate we have data (fail loudly if empty)
    if not all_repos:
        error_msg = "No repositories fetched from GitHub API. Aborting."
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    # Save to JSON file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_repos, f, indent=2)
        
        logger.info(f"Successfully saved {len(all_repos)} repositories to {output_file}")
        logger.info(f"Repository names saved: {[repo['name'] for repo in all_repos[:5]]}...")
        
    except IOError as e:
        logger.error(f"Failed to write output file: {e}")
        raise RuntimeError(f"Failed to write output file: {e}")
    
    logger.info("T012a completed successfully")

if __name__ == "__main__":
    main()
