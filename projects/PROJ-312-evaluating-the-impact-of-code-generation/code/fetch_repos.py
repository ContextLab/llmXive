import json
import logging
import os
import time
from pathlib import Path
from typing import List, Dict, Any

from utils import api_request_with_backoff

logger = logging.getLogger(__name__)

def fetch_repos_from_github(
    languages: List[str] = None,
    min_stars: int = 10000,
    limit_per_lang: int = 50
) -> List[Dict[str, Any]]:
    """
    Fetch top repositories by star count for specified languages using GitHub API.

    Args:
        languages: List of languages to query (e.g., ["Python", "JavaScript"])
        min_stars: Minimum star count threshold
        limit_per_lang: Maximum number of repos to fetch per language

    Returns:
        List of repository objects containing 'name' and 'stars'
    """
    if languages is None:
        languages = ["Python", "JavaScript"]

    all_repos = []

    for lang in languages:
        logger.info(f"Fetching top {limit_per_lang} {lang} repositories with > {min_stars} stars...")
        
        # Construct query: language:Python stars:>10000 sort:stars order:desc
        query = f"language:{lang} stars:>{min_stars}"
        url = "https://api.github.com/search/repositories"
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": 100,  # Max allowed per page
            "page": 1
        }

        fetched_count = 0
        page = 1

        while fetched_count < limit_per_lang:
            params["page"] = page
            
            try:
                response = api_request_with_backoff(url, params=params)
                
                if response is None:
                    logger.error(f"Failed to fetch page {page} for {lang} after retries")
                    break

                items = response.get("items", [])
                if not items:
                    logger.warning(f"No more items found for {lang} on page {page}")
                    break

                for item in items:
                    if fetched_count >= limit_per_lang:
                        break
                    
                    repo_data = {
                        "name": item["full_name"],
                        "stars": item["stargazers_count"],
                        "language": item["language"]
                    }
                    all_repos.append(repo_data)
                    fetched_count += 1

                # Check rate limit headers if available
                remaining = response.get("_headers", {}).get("X-RateLimit-Remaining")
                if remaining and int(remaining) < 10:
                    logger.warning(f"Approaching rate limit for {lang} ({remaining} remaining)")

                page += 1

            except Exception as e:
                logger.error(f"Error fetching repos for {lang}: {e}")
                break

        logger.info(f"Fetched {fetched_count} repositories for {lang}")

    return all_repos

def main():
    """
    Main entry point to fetch repositories and save to data/raw/repos.json
    """
    # Ensure output directory exists
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "repos.json"

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting repository fetch process...")

    try:
        # Fetch repositories
        repos = fetch_repos_from_github(
            languages=["Python", "JavaScript"],
            min_stars=10000,
            limit_per_lang=50
        )

        if not repos:
            logger.error("No repositories fetched. Check API connectivity and rate limits.")
            return 1

        # Save to JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(repos, f, indent=2)

        logger.info(f"Successfully saved {len(repos)} repositories to {output_path}")
        return 0

    except Exception as e:
        logger.exception(f"Fatal error in main: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
