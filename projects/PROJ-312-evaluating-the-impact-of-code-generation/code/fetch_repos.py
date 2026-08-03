import json
import logging
import os
import time
from pathlib import Path
from typing import List, Dict, Any

from utils import api_request_with_backoff
from logging_config import get_logger

# Configure logger
logger = get_logger(__name__)

def fetch_repos_from_github(language: str, min_stars: int = 10000, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Fetch a representative set of top repositories for a given language using GitHub API.
    
    Args:
        language: Language filter (e.g., 'Python', 'JavaScript')
        min_stars: Minimum star count threshold
        limit: Maximum number of repositories to fetch
    
    Returns:
        List of repository objects with 'name' and 'stars'
    """
    base_url = "https://api.github.com/search/repositories"
    query = f"language:{language}+stars:>{min_stars}"
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": limit
    }
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "llmXive-Research-Pipeline"
    }
    
    logger.info(f"Fetching top {limit} {language} repositories with >{min_stars} stars...")
    
    try:
        response = api_request_with_backoff(base_url, headers, params=params)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch repositories: {response.status_code} - {response.text}")
            return []
        
        data = response.json()
        items = data.get("items", [])
        
        repos = []
        for item in items[:limit]:
            repos.append({
                "name": item["full_name"],
                "stars": item["stargazers_count"]
            })
        
        logger.info(f"Successfully fetched {len(repos)} repositories for {language}")
        return repos
        
    except Exception as e:
        logger.error(f"Error fetching repositories for {language}: {e}")
        raise

def main():
    """
    Main entry point for fetching repository data.
    Fetches top Python and JavaScript repositories and saves to data/raw/repos.json
    """
    # Ensure output directory exists
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "repos.json"
    
    all_repos = []
    
    # Fetch Python repositories
    python_repos = fetch_repos_from_github("Python", min_stars=10000, limit=50)
    all_repos.extend(python_repos)
    
    # Fetch JavaScript repositories
    js_repos = fetch_repos_from_github("JavaScript", min_stars=10000, limit=50)
    all_repos.extend(js_repos)
    
    # Deduplicate by name (in case of overlap)
    seen_names = set()
    unique_repos = []
    for repo in all_repos:
        if repo["name"] not in seen_names:
            seen_names.add(repo["name"])
            unique_repos.append(repo)
    
    # Sort by stars descending
    unique_repos.sort(key=lambda x: x["stars"], reverse=True)
    
    logger.info(f"Total unique repositories collected: {len(unique_repos)}")
    
    # Save to JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(unique_repos, f, indent=2)
    
    logger.info(f"Repository data saved to {output_file}")
    print(f"Saved {len(unique_repos)} repositories to {output_file}")

if __name__ == "__main__":
    main()