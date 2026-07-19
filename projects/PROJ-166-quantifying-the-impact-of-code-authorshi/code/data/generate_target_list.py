import os
import sys
import time
import requests
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import ensure_directories

GITHUB_API_URL = "https://api.github.com/search/repositories"
OUTPUT_PATH = Path("data/raw/target_list.csv")

# A curated list of popular repos across languages to ensure a robust dataset
# We use specific queries to fetch real data from GitHub API.
SEARCH_QUERIES = [
    "language:python stars:>10000",
    "language:javascript stars:>10000",
    "language:go stars:>5000",
    "language:java stars:>5000",
    "language:rust stars:>5000",
]

def fetch_repo_metadata(query: str, per_page: int = 10) -> list:
    """Fetch repository metadata from GitHub API."""
    repos = []
    page = 1
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "llmXive-Pipeline"
    }
    
    # If API key is available (T029), use it
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    while len(repos) < per_page:
        try:
            params = {"q": query, "sort": "stars", "order": "desc", "per_page": 10, "page": page}
            response = requests.get(GITHUB_API_URL, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            items = data.get("items", [])
            if not items:
                break
            
            for item in items:
                repos.append({
                    "url": item["html_url"],
                    "language": item.get("language", "Unknown"),
                    "stars": item["stargazers_count"],
                    "created_at": item["created_at"]
                })
                if len(repos) >= per_page:
                    break
            
            page += 1
            time.sleep(1) # Rate limit safety
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {query}: {e}")
            break
    
    return repos

def generate_target_list():
    """Generate the target list CSV."""
    ensure_directories()
    
    all_repos = []
    for query in SEARCH_QUERIES:
        print(f"Fetching repos for query: {query}")
        repos = fetch_repo_metadata(query, per_page=10)
        all_repos.extend(repos)
    
    if not all_repos:
        raise RuntimeError("Failed to fetch any repositories from GitHub API.")
    
    # Convert to DataFrame
    df = pd.DataFrame(all_repos)
    
    # Calculate age in years
    df['created_at'] = pd.to_datetime(df['created_at'])
    now = datetime.now(timezone.utc)
    df['age'] = (now - df['created_at']).dt.days / 365.25
    
    # Select and order columns
    # Explicitly map 'language' to 'primary_language' as per task requirements
    df = df[['url', 'language', 'stars', 'age']]
    df = df.rename(columns={'language': 'primary_language'})
    
    # Sort by URL alphabetically (as per T006 requirement)
    df = df.sort_values(by='url').reset_index(drop=True)
    
    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to CSV
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Target list saved to {OUTPUT_PATH} with {len(df)} entries.")
    
    # Verification: Assert file exists and contains exactly len(target_list) rows
    assert OUTPUT_PATH.exists(), f"Output file {OUTPUT_PATH} was not created."
    loaded_df = pd.read_csv(OUTPUT_PATH)
    assert len(loaded_df) == len(df), f"Row count mismatch: expected {len(df)}, got {len(loaded_df)}"
    
    return df

def main():
    generate_target_list()

if __name__ == "__main__":
    main()