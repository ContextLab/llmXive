"""
Module to fetch a target list of repositories via GitHub API.
Implements T006: Fetch repos with min stars, handle rate limits, output CSV.
"""
import os
import sys
import time
import requests
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import TARGET_MIN_STARS, GITHUB_TOKEN, DATA_RAW_DIR, ensure_directories

# Constants
GITHUB_API_URL = "https://api.github.com/search/repositories"
MAX_RETRIES = 3
BASE_DELAY = 1.0  # seconds

def build_query():
    """
    Construct the GitHub search query string dynamically using TARGET_MIN_STARS.
    Returns a query string formatted for GitHub Search API.
    """
    # Query: stars >= TARGET_MIN_STARS, sort by stars descending, type repo
    # We fetch 'in:name,description' to ensure relevance, though stars is the main filter
    query = f"stars:>={TARGET_MIN_STARS} type:repo sort:stars desc"
    return query

def fetch_repo_metadata(query, per_page=100, max_pages=5):
    """
    Fetch repository metadata from GitHub API with exponential backoff.
    
    Args:
        query (str): GitHub search query string.
        per_page (int): Number of results per page.
        max_pages (int): Maximum number of pages to fetch.
    
    Returns:
        list: List of dictionaries containing repo metadata.
    
    Raises:
        SystemExit: On critical errors (403, failed retries).
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    all_repos = []
    page = 1
    
    while page <= max_pages:
        params = {
            "q": query,
            "per_page": per_page,
            "page": page,
        }
        
        attempt = 0
        success = False
        
        while attempt < MAX_RETRIES:
            try:
                response = requests.get(GITHUB_API_URL, headers=headers, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get("items", [])
                    all_repos.extend(items)
                    success = True
                    break  # Success, move to next page
                elif response.status_code == 403:
                    # Forbidden (likely rate limit without token or auth issue)
                    sys.stderr.write(f"CRITICAL: GitHub API returned 403 Forbidden. "
                                   f"Check GITHUB_TOKEN environment variable.\n")
                    sys.exit(1)
                elif response.status_code == 429:
                    # Too Many Requests - Rate Limited
                    sys.stderr.write(f"WARNING: Rate limit hit (429). Retrying with backoff...\n")
                    attempt += 1
                    if attempt >= MAX_RETRIES:
                        sys.stderr.write("CRITICAL: Max retries exceeded for rate limit.\n")
                        sys.exit(1)
                    # Exponential backoff with jitter
                    delay = BASE_DELAY * (2 ** (attempt - 1)) + (time.time() % 0.5)
                    time.sleep(delay)
                    continue
                else:
                    # Other error
                    sys.stderr.write(f"ERROR: Unexpected status code {response.status_code}: {response.text}\n")
                    attempt += 1
                    if attempt >= MAX_RETRIES:
                        sys.exit(1)
                    time.sleep(BASE_DELAY)
                    
            except requests.exceptions.RequestException as e:
                sys.stderr.write(f"ERROR: Request failed: {e}\n")
                attempt += 1
                if attempt >= MAX_RETRIES:
                    sys.exit(1)
                time.sleep(BASE_DELAY)
        
        if not success:
            sys.exit(1)
        
        # Check if we have more results
        total_count = data.get("total_count", 0)
        if len(all_repos) >= total_count:
            break
        
        page += 1
        
        # GitHub API rate limit for search is generous but we should be polite
        # Small sleep between pages
        time.sleep(1.0)
    
    return all_repos

def generate_target_list():
    """
    Main logic to generate the target list CSV.
    
    Returns:
        pd.DataFrame: DataFrame with columns: url, primary_language, stars, age.
    """
    ensure_directories()
    
    query = build_query()
    sys.stdout.write(f"Fetching repositories with query: '{query}' (min stars: {TARGET_MIN_STARS})\n")
    
    repos = fetch_repo_metadata(query)
    
    if not repos:
        sys.stderr.write("ERROR: No repositories found matching the query.\n")
        sys.exit(1)
    
    data = []
    for repo in repos:
        url = repo.get("html_url", "")
        primary_language = repo.get("language") or "Unknown"
        stars = repo.get("stargazers_count", 0)
        created_at = repo.get("created_at")
        
        # Calculate age in years
        age_years = None
        if created_at:
            try:
                created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                age_years = (now - created_dt).days / 365.25
            except ValueError:
                age_years = 0.0
        
        data.append({
            "url": url,
            "primary_language": primary_language,
            "stars": stars,
            "age": age_years
        })
    
    df = pd.DataFrame(data)
    
    # Ensure output directory exists
    output_path = DATA_RAW_DIR / "target_list.csv"
    df.to_csv(output_path, index=False)
    
    sys.stdout.write(f"Successfully wrote {len(df)} repositories to {output_path}\n")
    
    return df

def main():
    """Entry point for the script."""
    generate_target_list()

if __name__ == "__main__":
    main()
