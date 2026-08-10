"""
Repository Metadata Enrichment Script (T045).

Fetches metadata (language, star_count, contributor_count) for repositories
present in the dataset via the GitHub API and merges 'language' into the
main dataset.

Outputs:
    1. data/processed/repo_metadata.json
    2. Updates data/processed/cleaned_issues.csv (in-place or new file) to include 'language'
"""

import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple

import pandas as pd
import requests

# Import project configuration
from utils.config import get_config, get_path

# Import API client utilities
from utils.api_client import get_headers, handle_rate_limit

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("data/logs/enrich_metadata.log")
    ]
)
logger = logging.getLogger(__name__)

# Constants
GITHUB_API_BASE = "https://api.github.com/repos"
RATE_LIMIT_WAIT = 60  # Seconds to wait on 403/429

def load_repository_list() -> Set[str]:
    """
    Extracts unique repository identifiers (owner/repo) from the raw or merged dataset.
    Assumes the dataset is in parquet format under data/raw/ or data/processed/.
    """
    # Determine source file: prefer merged if exists, else raw
    merged_path = get_path("data/raw/github_issues_raw_merged.parquet")
    raw_hf_path = get_path("data/raw/github_issues_raw_hf.parquet")
    raw_api_path = get_path("data/raw/github_issues_raw_api.parquet")

    source_path = None
    if merged_path.exists():
        source_path = merged_path
    elif raw_hf_path.exists():
        source_path = raw_hf_path
    elif raw_api_path.exists():
        source_path = raw_api_path
    else:
        raise FileNotFoundError(
            "No raw dataset found. Please run T009c (Orchestrator) first to generate data."
        )

    logger.info(f"Loading repository list from: {source_path}")
    df = pd.read_parquet(source_path)

    # Identify column name for repository identifier
    # Common names: 'repo', 'repository', 'full_name', 'owner_repo'
    repo_col_candidates = ['full_name', 'repo', 'repository', 'owner_repo', 'repo_name']
    repo_col = None
    for candidate in repo_col_candidates:
        if candidate in df.columns:
            repo_col = candidate
            break

    if not repo_col:
        # Fallback: try to find a column that looks like "owner/repo"
        for col in df.columns:
            if df[col].dtype == 'object' and df[col].str.contains('/').any():
                repo_col = col
                break

    if not repo_col:
        raise ValueError("Could not identify repository identifier column in dataset.")

    unique_repos = set(df[repo_col].dropna().unique())
    logger.info(f"Found {len(unique_repos)} unique repositories.")
    return unique_repos

def fetch_repo_metadata(repo_id: str, token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Fetches metadata for a single repository from GitHub API.
    Returns dict with {repo_id, language, star_count, contributor_count} or None on failure.
    """
    headers = get_headers(token)
    url = f"{GITHUB_API_BASE}/{repo_id}"

    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "repo_id": repo_id,
                "language": data.get("language"),
                "star_count": data.get("stargazers_count", 0),
                "contributor_count": data.get("subscribers_count", 0) # Using subscribers as proxy if contributors endpoint is slow, or fetch contributors
            }
        elif response.status_code == 404:
            logger.warning(f"Repository not found: {repo_id}")
            return None
        elif response.status_code == 403:
            # Rate limit hit
            logger.warning(f"Rate limit hit for {repo_id}. Waiting {RATE_LIMIT_WAIT}s.")
            time.sleep(RATE_LIMIT_WAIT)
            # Retry once
            retry_response = requests.get(url, headers=headers, timeout=30)
            if retry_response.status_code == 200:
                data = retry_response.json()
                return {
                    "repo_id": repo_id,
                    "language": data.get("language"),
                    "star_count": data.get("stargazers_count", 0),
                    "contributor_count": data.get("subscribers_count", 0)
                }
            else:
                logger.error(f"Rate limit still active after wait. Aborting fetch for {repo_id}.")
                return None
        else:
            logger.error(f"API Error {response.status_code} for {repo_id}: {response.text[:100]}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for {repo_id}: {e}")
        return None

def enrich_metadata() -> Tuple[Dict[str, Any], pd.DataFrame]:
    """
    Main logic:
    1. Load repo list.
    2. Fetch metadata for each.
    3. Save metadata to JSON.
    4. Merge 'language' into the main dataset.
    5. Save updated dataset.
    """
    config = get_config()
    api_token = config.get("github", {}).get("token") or None

    unique_repos = load_repository_list()
    metadata_list = []
    
    logger.info(f"Starting metadata fetch for {len(unique_repos)} repositories...")
    
    for i, repo_id in enumerate(unique_repos):
        if (i + 1) % 10 == 0:
            logger.info(f"Processed {i + 1}/{len(unique_repos)} repos...")
        
        meta = fetch_repo_metadata(repo_id, api_token)
        if meta:
            metadata_list.append(meta)
        
        # Small delay to be polite to API
        time.sleep(0.1)

    # Save metadata to JSON
    output_meta_path = get_path("data/processed/repo_metadata.json")
    output_meta_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_meta_path, 'w', encoding='utf-8') as f:
        json.dump(metadata_list, f, indent=2)
    logger.info(f"Saved metadata to {output_meta_path}")

    # Create DataFrame for merging
    meta_df = pd.DataFrame(metadata_list)
    
    # Load the main dataset again to merge
    merged_path = get_path("data/raw/github_issues_raw_merged.parquet")
    if not merged_path.exists():
        # Fallback to raw if merged doesn't exist (should be covered by load_repository_list logic)
        if get_path("data/raw/github_issues_raw_hf.parquet").exists():
            merged_path = get_path("data/raw/github_issues_raw_hf.parquet")
        elif get_path("data/raw/github_issues_raw_api.parquet").exists():
            merged_path = get_path("data/raw/github_issues_raw_api.parquet")
    
    df_main = pd.read_parquet(merged_path)

    # Identify repo column
    repo_col = None
    candidates = ['full_name', 'repo', 'repository', 'owner_repo', 'repo_name']
    for c in candidates:
        if c in df_main.columns:
            repo_col = c
            break
    if not repo_col:
        for col in df_main.columns:
            if df_main[col].dtype == 'object' and df_main[col].str.contains('/').any():
                repo_col = col
                break
    
    if not repo_col:
        raise ValueError("Could not identify repository column in main dataset for merging.")

    # Rename meta_df column to match
    meta_df = meta_df.rename(columns={"repo_id": repo_col})

    # Merge left to keep all issues
    df_enriched = df_main.merge(
        meta_df[[repo_col, "language"]], 
        on=repo_col, 
        how="left"
    )

    # Save updated dataset
    output_cleaned_path = get_path("data/processed/cleaned_issues.csv")
    output_cleaned_path.parent.mkdir(parents=True, exist_ok=True)
    
    df_enriched.to_csv(output_cleaned_path, index=False)
    logger.info(f"Saved enriched dataset to {output_cleaned_path}")

    return {"metadata_count": len(metadata_list)}, df_enriched

def main():
    logger.info("Starting Repository Metadata Enrichment (T045)...")
    try:
        stats, df = enrich_metadata()
        logger.info(f"Enrichment complete. Fetched {stats['metadata_count']} metadata records.")
        return 0
    except Exception as e:
        logger.error(f"Enrichment failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())