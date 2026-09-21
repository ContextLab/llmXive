import json
import logging
import os
import time
from pathlib import Path
from typing import List, Dict, Any

from utils import api_request_with_backoff, log_api_headers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def fetch_repos_from_github(language: str, min_stars: int = 10000, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Fetch top repositories for a given language sorted by stars.
    
    Args:
        language: Language to filter by (e.g., 'Python', 'JavaScript')
        min_stars: Minimum star count filter
        limit: Maximum number of repos to return
        
    Returns:
        List of repository dictionaries with 'name' and 'stars' keys
    """
    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN environment variable is not set")

    query = f"language:{language}+stars:>{min_stars}&sort=stars&order=desc"
    url = f"{GITHUB_API_BASE}/search/repositories?q={query}&per_page=100"
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {GITHUB_TOKEN}"
    }

    all_repos = []
    page = 1
    
    while len(all_repos) < limit:
        params = {"page": page, "per_page": 100}
        
        try:
            response = api_request_with_backoff(url, headers, params=params)
            log_api_headers(response)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch repos for {language}: {response.status_code} - {response.text}")
                break
            
            data = response.json()
            items = data.get("items", [])
            
            if not items:
                logger.info(f"No more items found for {language}")
                break
            
            # Extract only name and stars as per spec
            for repo in items:
                if len(all_repos) >= limit:
                    break
                all_repos.append({
                    "name": repo["full_name"],
                    "stars": repo["stargazers_count"]
                })
            
            page += 1
            
        except Exception as e:
            logger.error(f"Error fetching page {page} for {language}: {e}")
            break
    
    logger.info(f"Fetched {len(all_repos)} repositories for language: {language}")
    return all_repos

def main():
    """Main entry point to fetch repos and save to data/raw/repos.json"""
    project_root = Path(__file__).resolve().parent.parent
    output_path = project_root / "data" / "raw" / "repos.json"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting repository fetch. Output will be saved to: {output_path}")
    
    all_repos = []
    
    # Fetch Python repos
    logger.info("Fetching top Python repositories...")
    python_repos = fetch_repos_from_github("Python", min_stars=10000, limit=50)
    all_repos.extend(python_repos)
    
    # Fetch JavaScript repos
    logger.info("Fetching top JavaScript repositories...")
    js_repos = fetch_repos_from_github("JavaScript", min_stars=10000, limit=50)
    all_repos.extend(js_repos)
    
    # Deduplicate by repo name if any overlap exists (unlikely but safe)
    seen_names = set()
    unique_repos = []
    for repo in all_repos:
        if repo["name"] not in seen_names:
            seen_names.add(repo["name"])
            unique_repos.append(repo)
    
    logger.info(f"Total unique repositories collected: {len(unique_repos)}")
    
    # Save to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(unique_repos, f, indent=2)
    
    logger.info(f"Successfully saved {len(unique_repos)} repositories to {output_path}")
    
    return unique_repos

if __name__ == "__main__":
    main()
