"""
Repository Metadata Enrichment Script (T045).

Fetches 'language', 'star_count', and 'contributor_count' for repositories
in the dataset via GitHub API.
Outputs to 'data/processed/repo_metadata.json' with schema:
{repo_id, language, star_count, contributor_count}
and merges 'language' into the main dataset before writing the raw parquet file.
"""
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple

import pandas as pd
import requests

# Import shared utilities from the project's API surface
from utils.config import get_config, get_path
from utils.api_client import GitHubAPIClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(get_path("logs/enrich_metadata.log")),
    ],
)
logger = logging.getLogger(__name__)

# Constants
GITHUB_API_BASE = "https://api.github.com"
BATCH_SIZE = 10  # Process repos in batches to manage API calls
RETRY_DELAY = 60  # Seconds to wait on rate limit

def load_repository_list(input_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Loads the list of repositories from the raw dataset.
    If input_path is not provided, uses the default raw data path.
    Returns a list of dicts with repo identifiers.
    """
    if input_path is None:
        input_path = get_path("raw/github_issues_raw_hf.parquet")
        if not input_path.exists():
            # Fallback to API raw path if HF doesn't exist yet
            input_path = get_path("raw/github_issues_raw_api.parquet")

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input raw data file not found: {input_path}. "
            "T045 must run after data collection (T009a/T009b) but before "
            "the Orchestrator writes the final parquet."
        )

    logger.info(f"Loading repository list from {input_path}")
    try:
        df = pd.read_parquet(input_path)
    except Exception as e:
        # Fallback to CSV if parquet fails (e.g., if API loader wrote CSV first)
        logger.warning(f"Parquet read failed: {e}. Trying CSV fallback.")
        csv_path = input_path.with_suffix('.csv')
        if csv_path.exists():
            df = pd.read_csv(csv_path)
        else:
            raise RuntimeError(f"Could not read input data from {input_path} or {csv_path}")

    # Extract unique repositories
    # Assumes columns 'repository_id' or 'repo_id' exist.
    # If not, try to infer from 'full_name' or 'html_url'
    repo_col = None
    for col in ['repository_id', 'repo_id', 'full_name']:
        if col in df.columns:
            repo_col = col
            break

    if repo_col is None:
        raise ValueError("Could not find repository identifier column in raw data.")

    unique_repos = df[repo_col].dropna().unique().tolist()
    logger.info(f"Found {len(unique_repos)} unique repositories to enrich.")
    return unique_repos

def fetch_repo_metadata(
    repo_id: str,
    client: GitHubAPIClient
) -> Optional[Dict[str, Any]]:
    """
    Fetches metadata for a single repository from GitHub API.
    Returns dict with {repo_id, language, star_count, contributor_count}
    or None if fetch fails.
    """
    # Normalize repo_id to full_name if it's just an ID
    # GitHub API expects owner/repo format.
    # If repo_id is a URL or numeric ID, we need to resolve it.
    # Assuming repo_id is 'owner/repo' based on typical GitHub issue data.
    if not repo_id or '/' not in repo_id:
        logger.warning(f"Invalid repo_id format: {repo_id}. Skipping.")
        return None

    url = f"{GITHUB_API_BASE}/repos/{repo_id}"
    headers = {"Accept": "application/vnd.github.v3+json"}

    try:
        response = client.get(url, headers=headers)
        if response.status_code == 404:
            logger.warning(f"Repository not found: {repo_id}")
            return None
        if response.status_code == 403:
            # Rate limit or other block
            logger.error(f"API blocked for {repo_id}: {response.status_code}")
            return None
        response.raise_for_status()

        data = response.json()
        return {
            "repo_id": repo_id,
            "language": data.get("language"),
            "star_count": data.get("stargazers_count", 0),
            "contributor_count": data.get("subscribers_count", 0) # Fallback if contributors endpoint is too expensive
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch metadata for {repo_id}: {e}")
        return None

def enrich_metadata(
    repo_list: List[str],
    client: GitHubAPIClient,
    output_path: Path
) -> Dict[str, Any]:
    """
    Iterates through the repo list, fetches metadata, and saves to JSON.
    Also returns the merged dataset with 'language' added if possible.
    """
    metadata_map = {}
    failed_count = 0

    logger.info(f"Starting metadata enrichment for {len(repo_list)} repositories.")

    for i, repo_id in enumerate(repo_list):
        if i > 0 and i % BATCH_SIZE == 0:
            # Small delay to be polite to API
            time.sleep(0.5)

        result = fetch_repo_metadata(repo_id, client)
        if result:
            metadata_map[repo_id] = result
        else:
            failed_count += 1

        # Log progress
        if (i + 1) % 50 == 0:
            logger.info(f"Processed {i+1}/{len(repo_list)} repos. Failed so far: {failed_count}")

    # Save metadata to JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata_map, f, indent=2)
    logger.info(f"Saved metadata to {output_path}")

    return metadata_map

def main():
    """
    Main entry point for T045.
    1. Load raw data to get repo list.
    2. Fetch metadata via API.
    3. Save metadata JSON.
    4. Merge 'language' back into the raw dataset (in memory or file).
    """
    config = get_config()
    raw_input_path = get_path("raw/github_issues_raw_hf.parquet")
    if not raw_input_path.exists():
        raw_input_path = get_path("raw/github_issues_raw_api.parquet")

    metadata_output_path = get_path("processed/repo_metadata.json")
    final_raw_output_path = get_path("raw/github_issues_raw_enriched.parquet")

    logger.info("Starting Repository Metadata Enrichment (T045)")

    # Initialize API Client
    client = GitHubAPIClient()

    # Load repo list
    try:
        repo_list = load_repository_list(raw_input_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    if not repo_list:
        logger.warning("No repositories found to enrich. Exiting.")
        sys.exit(0)

    # Enrich metadata
    metadata_map = enrich_metadata(repo_list, client, metadata_output_path)

    # Merge language into main dataset
    logger.info("Merging 'language' into main dataset...")
    try:
        df = pd.read_parquet(raw_input_path)
    except Exception:
        # Fallback to CSV
        csv_path = raw_input_path.with_suffix('.csv')
        df = pd.read_csv(csv_path)

    # Determine column name for repo ID
    repo_col = None
    for col in ['repository_id', 'repo_id', 'full_name']:
        if col in df.columns:
            repo_col = col
            break

    if repo_col:
        # Map language from metadata_map
        def get_language(repo_id):
            if repo_id in metadata_map:
                return metadata_map[repo_id].get('language')
            return None

        df['language'] = df[repo_col].apply(get_language)
        logger.info(f"Added 'language' column. Non-null count: {df['language'].notna().sum()}")

        # Save enriched raw data
        final_raw_output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(final_raw_output_path, index=False)
        logger.info(f"Saved enriched raw data to {final_raw_output_path}")
    else:
        logger.error("Could not determine repository ID column for merging.")
        sys.exit(1)

    logger.info("T045 completed successfully.")

if __name__ == "__main__":
    main()
