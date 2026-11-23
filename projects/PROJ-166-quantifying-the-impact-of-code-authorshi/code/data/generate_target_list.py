"""
Module to fetch a target list of repositories via GitHub API.

Implements T006:
- Constructs query using TARGET_MIN_STARS from config.
- Handles authentication via GITHUB_TOKEN env var.
- Implements exponential backoff with jitter for HTTP 429.
- Aborts on HTTP 403.
- Retries max 3 times per query.
- Outputs data/raw/target_list.csv with columns: url, primary_language, stars, age.
"""
import os
import sys
import time
import requests
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
import logging
import random

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import TARGET_MIN_STARS, GITHUB_TOKEN, DATA_RAW_DIR, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(DATA_RAW_DIR / 'generate_target_list.log') if DATA_RAW_DIR.exists() else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com/search/repositories"
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0
MAX_BACKOFF = 60.0

def build_query(min_stars: int) -> str:
    """
    Constructs the GitHub search query string.
    Uses the static variable TARGET_MIN_STARS from config.
    """
    # Query for public repos with at least min_stars, sorted by stars descending
    query = f"stars:>={min_stars} is:public"
    logger.info(f"Constructed query: {query}")
    return query

def fetch_repo_metadata(query: str, output_path: Path) -> None:
    """
    Fetches repository metadata from GitHub API and saves to CSV.
    
    Implements exponential backoff with jitter for 429 errors.
    Aborts on 403.
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "llmXive-research-pipeline"
    }
    
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    else:
        logger.warning("GITHUB_TOKEN not found in environment. Rate limits will be strict.")

    all_repos = []
    page = 1
    per_page = 100
    
    while True:
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": per_page,
            "page": page
        }
        
        attempt = 0
        success = False
        
        while attempt < MAX_RETRIES:
            try:
                logger.info(f"Fetching page {page} (Attempt {attempt + 1}/{MAX_RETRIES})...")
                response = requests.get(GITHUB_API_BASE, headers=headers, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get("items", [])
                    
                    if not items:
                        logger.info("No more items found.")
                        success = True
                        break
                    
                    for repo in items:
                        # Calculate age in years
                        created_at_str = repo.get("created_at", "")
                        try:
                            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                            age_years = (datetime.now(timezone.utc) - created_at).days / 365.25
                        except (ValueError, TypeError):
                            age_years = 0.0
                        
                        all_repos.append({
                            "url": repo.get("html_url", ""),
                            "primary_language": repo.get("language", "Unknown"),
                            "stars": repo.get("stargazers_count", 0),
                            "age": round(age_years, 2)
                        })
                    
                    # Check if we have more pages
                    if len(items) < per_page:
                        success = True
                        break
                    
                    page += 1
                    success = True
                    break
                    
                elif response.status_code == 403:
                    logger.critical(f"HTTP 403 Forbidden received. Aborting. Response: {response.text}")
                    raise RuntimeError("GitHub API returned 403 Forbidden. Check token or rate limit.")
                    
                elif response.status_code == 429:
                    attempt += 1
                    if attempt >= MAX_RETRIES:
                        logger.error("Max retries reached for HTTP 429. Aborting.")
                        raise RuntimeError("Max retries reached for HTTP 429 rate limit.")
                    
                    # Exponential backoff with jitter
                    backoff = min(INITIAL_BACKOFF * (2 ** (attempt - 1)) + random.uniform(0, 1), MAX_BACKOFF)
                    logger.warning(f"HTTP 429 Rate Limit. Retrying in {backoff:.2f}s (Attempt {attempt}/{MAX_RETRIES})...")
                    time.sleep(backoff)
                    continue
                    
                else:
                    logger.error(f"Unexpected status code: {response.status_code}. Response: {response.text}")
                    attempt += 1
                    if attempt >= MAX_RETRIES:
                        raise RuntimeError(f"Failed after {MAX_RETRIES} attempts. Status: {response.status_code}")
                    time.sleep(INITIAL_BACKOFF)
                    
            except requests.exceptions.RequestException as e:
                attempt += 1
                logger.error(f"Request error: {e}. Retrying...")
                if attempt >= MAX_RETRIES:
                    raise RuntimeError(f"Network error after {MAX_RETRIES} attempts.")
                time.sleep(INITIAL_BACKOFF)
        
        if not success:
            break

    if not all_repos:
        logger.warning("No repositories fetched. Output file will be empty.")
    
    df = pd.DataFrame(all_repos)
    
    # Ensure columns are in correct order
    expected_cols = ["url", "primary_language", "stars", "age"]
    if not df.empty:
        df = df[expected_cols]
    
    # Save to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Successfully saved {len(df)} repositories to {output_path}")

def generate_target_list() -> None:
    """
    Main entry point to generate the target list.
    """
    ensure_directories()
    output_path = DATA_RAW_DIR / "target_list.csv"
    query = build_query(TARGET_MIN_STARS)
    fetch_repo_metadata(query, output_path)

def main():
    """
    CLI entry point.
    """
    try:
        generate_target_list()
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
