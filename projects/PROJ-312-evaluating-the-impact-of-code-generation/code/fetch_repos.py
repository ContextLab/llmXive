import json
import logging
import os
import time
from pathlib import Path
from typing import List, Dict, Any

from utils import api_request_with_backoff, log_api_headers

# Constants
GITHUB_API_BASE = "https://api.github.com"
PYTHON_QUERY = "language:Python+stars:>10000"
JS_QUERY = "language:JavaScript+stars:>10000"
SORT_BY = "stars"
ORDER = "desc"
PER_PAGE = 100
TARGET_COUNT = 20

def fetch_repos_from_github(language: str, query: str, target_count: int = TARGET_COUNT) -> List[Dict[str, Any]]:
    """
    Fetches top repositories for a specific language from the GitHub API.
    
    Args:
        language: The language string for logging (e.g., "Python")
        query: The search query string
        target_count: Number of repos to fetch (default 20)
        
    Returns:
        List of repository dictionaries containing 'name' and 'stars'.
    """
    url = f"{GITHUB_API_BASE}/search/repositories"
    params = {
        "q": query,
        "sort": SORT_BY,
        "order": ORDER,
        "per_page": PER_PAGE
    }
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "llmXive-Pipeline"
    }
    
    all_repos = []
    page = 1
    
    while len(all_repos) < target_count:
        params["page"] = page
        
        response = api_request_with_backoff(url, headers, params=params)
        
        if response is None:
            logging.error(f"Failed to fetch page {page} for {language} repositories after retries.")
            break
        
        log_api_headers(response)
        
        data = response.json()
        items = data.get("items", [])
        
        if not items:
            logging.warning(f"No more items found for {language} at page {page}.")
            break
        
        for repo in items:
            if len(all_repos) >= target_count:
                break
            
            repo_info = {
                "name": repo["full_name"],
                "stars": repo["stargazers_count"]
            }
            all_repos.append(repo_info)
        
        page += 1
        
        # Safety break if we've iterated too much without hitting target
        if page > 5:
            logging.warning(f"Reached page limit (5) for {language} before hitting target count.")
            break
    
    logging.info(f"Fetched {len(all_repos)} repositories for {language}.")
    return all_repos

def main():
    """
    Main entry point for T012a: Fetch top 20 Python and 20 JavaScript repos.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    project_root = Path(__file__).resolve().parent.parent
    output_dir = project_root / "data" / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "repos.json"
    
    python_repos = fetch_repos_from_github("Python", PYTHON_QUERY)
    js_repos = fetch_repos_from_github("JavaScript", JS_QUERY)
    
    all_repos = python_repos + js_repos
    
    if len(all_repos) < 40:
        logging.warning(f"Total repos fetched ({len(all_repos)}) is less than expected 40. Proceeding with available data.")
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_repos, f, indent=2)
    
    logging.info(f"Saved {len(all_repos)} repositories to {output_file}")
    return 0

if __name__ == "__main__":
    exit(main())
