"""
Fetch GitHub PR data with batch processing and exponential backoff.

This module implements the skeleton for fetching Pull Requests from GitHub,
including:
- Batch processing structure
- Exponential backoff logic for rate limiting
- Retry mechanism with a limited number of attempts
- Integration with project logging and config utilities
"""

import os
import time
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import requests

# Project imports
from utils.config import get_config_summary
from utils.logging import get_logger, setup_logging
from utils.seeds import set_global_seed

# Initialize logging
logger = get_logger(__name__)

# Constants
MAX_RETRIES = 5
BASE_BACKOFF_SECONDS = 2.0
MAX_BACKOFF_SECONDS = 60.0
BATCH_SIZE = 100
OUTPUT_DIR = Path("data/raw")

def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_prs_from_repo(
    owner: str,
    repo: str,
    max_prs: int = 200,
    retries: int = MAX_RETRIES
) -> List[Dict[str, Any]]:
    """
    Fetch PRs from a specific GitHub repository with exponential backoff.
    
    Args:
        owner: Repository owner (e.g., 'psf')
        repo: Repository name (e.g., 'requests')
        max_prs: Maximum number of PRs to fetch
        retries: Maximum number of retry attempts
        
    Returns:
        List of PR data dictionaries
        
    Raises:
        requests.RequestException: If all retries fail
    """
    prs = []
    page = 1
    per_page = 100
    
    # Get API token from environment if available
    token = os.getenv("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    params = {"state": "all", "per_page": per_page, "page": page}
    
    logger.info(f"Fetching PRs from {owner}/{repo}")
    
    while len(prs) < max_prs:
        attempt = 0
        while attempt < retries:
            try:
                response = requests.get(url, headers=headers, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if not data:
                        logger.info(f"No more PRs found for {owner}/{repo}")
                        return prs
                    
                    prs.extend(data)
                    if len(prs) >= max_prs:
                        prs = prs[:max_prs]
                        break
                    
                    page += 1
                    params["page"] = page
                    break  # Success, break retry loop
                
                elif response.status_code == 403:
                    # Rate limited
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        wait_time = int(retry_after)
                    else:
                        wait_time = BASE_BACKOFF_SECONDS * (2 ** attempt)
                    
                    logger.warning(f"Rate limited. Waiting {wait_time} seconds before retry.")
                    time.sleep(wait_time)
                    attempt += 1
                
                else:
                    logger.error(f"API error {response.status_code}: {response.text}")
                    attempt += 1
            
            except requests.RequestException as e:
                logger.error(f"Request failed: {e}")
                attempt += 1
                if attempt < retries:
                    backoff = min(BASE_BACKOFF_SECONDS * (2 ** attempt), MAX_BACKOFF_SECONDS)
                    logger.info(f"Retrying in {backoff} seconds...")
                    time.sleep(backoff)
        
        if attempt == retries:
            raise requests.RequestException(
                f"Failed to fetch PRs from {owner}/{repo} after {retries} retries"
            )
    
    return prs

def save_prs_to_raw(prs: List[Dict[str, Any]], repo_slug: str) -> Path:
    """
    Save fetched PRs to raw data directory with checksum.
    
    Args:
        prs: List of PR dictionaries
        repo_slug: Repository slug (e.g., 'psf-requests')
        
    Returns:
        Path to the saved file
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"prs_{repo_slug}_{timestamp}.json"
    file_path = OUTPUT_DIR / filename
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(prs, f, indent=2, default=str)
    
    checksum = calculate_checksum(file_path)
    checksum_path = OUTPUT_DIR / f"{filename}.sha256"
    with open(checksum_path, "w") as f:
        f.write(f"{checksum}  {filename}\n")
    
    logger.info(f"Saved {len(prs)} PRs to {file_path} (checksum: {checksum[:16]}...)")
    return file_path

def run_batch_fetch() -> Dict[str, Any]:
    """
    Execute batch fetching from configured repositories.
    
    Returns:
        Dictionary with fetch statistics and output paths
    """
    # Set seed for reproducibility (though not strictly needed for fetching)
    set_global_seed(42)
    
    # Load config
    config = get_config_summary()
    repos = config.get("repos", [])
    
    if not repos:
        logger.error("No repositories configured in config.py")
        return {"success": False, "error": "No repos configured"}
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_repos": len(repos),
        "successful_fetches": 0,
        "failed_fetches": 0,
        "total_prs_fetched": 0,
        "files": []
    }
    
    for repo_config in repos:
        owner = repo_config.get("owner")
        repo = repo_config.get("name")
        repo_slug = f"{owner}-{repo}"
        
        if not owner or not repo:
            logger.error(f"Invalid repo config: {repo_config}")
            results["failed_fetches"] += 1
            continue
        
        try:
            prs = fetch_prs_from_repo(owner, repo)
            
            if prs:
                file_path = save_prs_to_raw(prs, repo_slug)
                results["successful_fetches"] += 1
                results["total_prs_fetched"] += len(prs)
                results["files"].append({
                    "repo": repo_slug,
                    "pr_count": len(prs),
                    "file_path": str(file_path),
                    "checksum": calculate_checksum(file_path)
                })
                logger.info(f"Successfully fetched {len(prs)} PRs from {repo_slug}")
            else:
                logger.warning(f"No PRs fetched from {repo_slug}")
                results["failed_fetches"] += 1
        
        except requests.RequestException as e:
            logger.error(f"Failed to fetch from {repo_slug}: {e}")
            results["failed_fetches"] += 1
            continue
    
    logger.info(
        f"Batch fetch complete: {results['successful_fetches']}/{results['total_repos']} "
        f"repos successful, {results['total_prs_fetched']} total PRs fetched"
    )
    
    return results

def main():
    """Main entry point for the fetch script."""
    logger.info("Starting GitHub PR fetch pipeline")
    
    try:
        results = run_batch_fetch()
        
        # Save results summary
        summary_path = OUTPUT_DIR / "fetch_summary.json"
        with open(summary_path, "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Fetch summary saved to {summary_path}")
        
        if results["failed_fetches"] > 0:
            logger.warning(f"{results['failed_fetches']} repositories failed to fetch")
            return 1
        
        return 0
    
    except Exception as e:
        logger.exception(f"Pipeline failed with unhandled exception: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
