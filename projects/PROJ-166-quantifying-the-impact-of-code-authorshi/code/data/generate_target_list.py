import os
import sys
import time
import requests
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
import logging

# Import from project config to ensure paths are consistent
from config import ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants from task requirements
TARGET_COUNT = 600
MIN_ACCEPTABLE_COUNT = 500
MAX_STARS_THRESHOLD = 1000
MIN_STARS_THRESHOLD = 100
STARS_DECREMENT = 500
MAX_STARS_ITERATIONS = 3
MAX_RETRIES_PER_QUERY = 3
REQUEST_TIMEOUT = 30

# GitHub API endpoint
GITHUB_API_SEARCH_URL = "https://api.github.com/search/repositories"

# Target output file
OUTPUT_FILE = "data/raw/target_list.csv"


def build_query(stars_threshold: int, languages: list = None) -> str:
    """
    Construct the GitHub Search API query string.
    
    Args:
        stars_threshold: Minimum number of stars required.
        languages: List of programming languages to filter by.
        
    Returns:
        URL-encoded query string.
    """
    if languages is None:
        languages = ["JavaScript", "Python", "Java", "C++"]
    
    # Build language part of query (OR logic for languages)
    lang_query = "+".join([f"language:{lang}" for lang in languages])
    
    # Build full query
    query = (
        f"q=stars:>{stars_threshold}"
        f"+created:>=2015-01-01"
        f"+{lang_query}"
        f"&sort=stars&order=desc"
    )
    
    return query


def fetch_repo_metadata(query: str, retries: int = MAX_RETRIES_PER_QUERY) -> list:
    """
    Fetch repository metadata from GitHub Search API.
    
    Args:
        query: The search query string.
        retries: Number of retry attempts on failure.
        
    Returns:
        List of repository dictionaries with relevant metadata.
        
    Raises:
        RuntimeError: If all retry attempts fail.
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "llmXive-Research-Agent"
    }
    
    # Add GitHub token if available (avoids rate limiting)
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    
    last_error = None
    
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Fetching repositories (attempt {attempt}/{retries})...")
            response = requests.get(
                GITHUB_API_SEARCH_URL,
                params=query,
                headers=headers,
                timeout=REQUEST_TIMEOUT
            )
            
            response.raise_for_status()
            data = response.json()
            
            if "items" not in data:
                raise ValueError("Invalid response format: 'items' key missing")
            
            logger.info(f"Found {data.get('total_count', 0)} total matches, retrieving {len(data['items'])} items")
            return data["items"]
            
        except requests.exceptions.RequestException as e:
            last_error = e
            logger.warning(f"Request failed (attempt {attempt}/{retries}): {e}")
            time.sleep(2 ** attempt)  # Exponential backoff
        except ValueError as e:
            logger.error(f"Invalid response data: {e}")
            raise
    
    raise RuntimeError(f"All {retries} retry attempts failed: {last_error}")


def generate_target_list():
    """
    Main function to generate the target list of repositories.
    
    Implements fallback logic: if <500 repos found, lower stars threshold
    by 500 (max 3 iterations, min stars=100).
    
    Returns:
        DataFrame with columns: url, primary_language, stars, age
    """
    ensure_directories()  # Ensure data/raw exists
    
    stars_threshold = MAX_STARS_THRESHOLD
    all_repos = []
    languages = ["JavaScript", "Python", "Java", "C++"]
    
    for iteration in range(MAX_STARS_ITERATIONS):
        logger.info(f"Iteration {iteration + 1}: Searching for repos with stars > {stars_threshold}")
        
        query = build_query(stars_threshold, languages)
        
        try:
            items = fetch_repo_metadata(query)
        except RuntimeError as e:
            logger.error(f"Failed to fetch data: {e}")
            raise
        
        # Extract relevant fields
        for item in items:
            repo_data = {
                "url": item["html_url"],
                "primary_language": item.get("language") or "Unknown",
                "stars": item["stargazers_count"],
                "age": (datetime.now(timezone.utc) - datetime.fromisoformat(
                    item["created_at"].replace('Z', '+00:00')
                )).days
            }
            all_repos.append(repo_data)
        
        # Check if we have enough repos
        if len(all_repos) >= MIN_ACCEPTABLE_COUNT:
            logger.info(f"Successfully collected {len(all_repos)} repositories.")
            break
        
        # Fallback logic: lower threshold if not enough repos
        if iteration < MAX_STARS_ITERATIONS - 1:
            new_threshold = stars_threshold - STARS_DECREMENT
            if new_threshold < MIN_STARS_THRESHOLD:
                new_threshold = MIN_STARS_THRESHOLD
            
            if new_threshold == stars_threshold:
                logger.warning("Cannot lower stars threshold further.")
                break
                
            stars_threshold = new_threshold
            logger.info(f"Lowering stars threshold to {stars_threshold} for next iteration.")
    
    # Final check
    if len(all_repos) < MIN_ACCEPTABLE_COUNT:
        raise RuntimeError(
            f"Failed to collect minimum required repos ({MIN_ACCEPTABLE_COUNT}). "
            f"Only collected {len(all_repos)}."
        )
    
    # Create DataFrame and deduplicate by URL
    df = pd.DataFrame(all_repos)
    df = df.drop_duplicates(subset=["url"])
    
    # Sort by stars descending
    df = df.sort_values(by="stars", ascending=False)
    
    # Limit to target count if we have more
    if len(df) > TARGET_COUNT:
        df = df.head(TARGET_COUNT)
    
    logger.info(f"Final dataset: {len(df)} repositories")
    
    # Save to CSV
    output_path = Path(OUTPUT_FILE)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved target list to {output_path.absolute()}")
    
    # Verification
    assert output_path.exists(), "Output file was not created"
    assert len(df) >= MIN_ACCEPTABLE_COUNT, f"Only {len(df)} rows, expected >= {MIN_ACCEPTABLE_COUNT}"
    
    return df


def main():
    """Entry point for script execution."""
    try:
        df = generate_target_list()
        print(f"SUCCESS: Generated target list with {len(df)} repositories.")
        print(f"Output saved to: {OUTPUT_FILE}")
    except Exception as e:
        logger.error(f"Failed to generate target list: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
