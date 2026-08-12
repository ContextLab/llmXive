"""
code/data/fetch_github.py

Fetches Pull Requests from prioritized GitHub repositories, handling pagination,
API rate-limit backoff, and saving raw JSON payloads with SHA-256 checksums.

Implements Constitution Principle III: Data Integrity via checksumming.
"""
import os
import time
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests

from utils.logging import get_logger, setup_logging
from utils.config import get_config_summary
from utils.seeds import set_global_seed
from utils.checksum import calculate_checksum

# Setup logging
logger = get_logger(__name__)
setup_logging()

# Configuration
MAX_RETRIES = 5
INITIAL_BACKOFF = 1.0  # seconds
MAX_BACKOFF = 60.0     # seconds
TIMEOUT = 30           # seconds
WATCHDOG_TIMEOUT = 300 # seconds (5 minutes) to prevent CI hanging

# Prioritized repos from config (T005)
REPO_LIST = [
    "psf/requests",
    "microsoft/vscode",
    "numpy/numpy"
]

def calculate_checksum(file_path: Path) -> str:
    """
    Calculate SHA-256 checksum for a file.
    Delegates to utils.checksum.calculate_checksum for consistency.
    """
    return calculate_checksum(file_path)

def fetch_prs_from_repo(
    repo: str,
    output_dir: Path,
    max_prs: int = 200,
    token: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetches up to `max_prs` Pull Requests from a specific GitHub repository.
    Handles pagination, exponential backoff on rate limits, and saves raw JSON.

    Args:
        repo: Repository string in format "owner/repo".
        output_dir: Directory to save raw JSON files.
        max_prs: Maximum number of PRs to fetch.
        token: Optional GitHub API token.

    Returns:
        List of PR dictionaries.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "llmXive-research-pipeline"
    }
    if token:
        headers["Authorization"] = f"token {token}"

    base_url = f"https://api.github.com/repos/{repo}/pulls"
    params = {
        "state": "all",
        "per_page": 100,
        "sort": "created",
        "direction": "desc"
    }

    all_prs = []
    page = 1
    start_time = time.time()

    logger.info(f"Starting fetch for {repo} (max {max_prs} PRs)...")

    while len(all_prs) < max_prs:
        # Watchdog check
        if time.time() - start_time > WATCHDOG_TIMEOUT:
            logger.error(f"Watchdog timeout exceeded for {repo}. Exiting gracefully.")
            break

        params["page"] = page
        url = f"{base_url}?page={page}&per_page={params['per_page']}"

        try:
            logger.debug(f"Fetching page {page} for {repo}...")
            response = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)

            if response.status_code == 403:
                if "rate limit exceeded" in response.text.lower():
                    # Exponential Backoff
                    if page == 1:
                        logger.warning("Rate limit hit immediately. Waiting...")
                    backoff = min(INITIAL_BACKOFF * (2 ** (MAX_RETRIES - 1)), MAX_BACKOFF)
                    logger.info(f"Rate limit exceeded. Backing off for {backoff:.1f}s.")
                    time.sleep(backoff)
                    # Retry logic is handled by the loop structure implicitly via backoff
                    # but we need to ensure we don't increment page on failure
                    continue
                else:
                    logger.error(f"Forbidden (403) for {repo}. Check token permissions.")
                    raise RuntimeError(f"GitHub API Forbidden: {response.text}")

            response.raise_for_status()
            prs_page = response.json()

            if not prs_page:
                logger.info(f"No more PRs found for {repo} (page {page}).")
                break

            all_prs.extend(prs_page)
            logger.debug(f"Retrieved {len(prs_page)} PRs. Total: {len(all_prs)}")
            page += 1

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching {repo} page {page}: {e}")
            raise

    # Truncate if we got more than requested
    if len(all_prs) > max_prs:
        all_prs = all_prs[:max_prs]
        logger.info(f"Truncated to {max_prs} PRs for {repo}.")

    # Save raw JSON
    timestamp = int(time.time())
    safe_repo_name = repo.replace("/", "_")
    filename = f"{safe_repo_name}_prs_{timestamp}.json"
    file_path = output_dir / filename

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(all_prs, f, indent=2, ensure_ascii=False)

    # Calculate and save checksum
    checksum = calculate_checksum(file_path)
    checksum_file = output_dir / f"{filename}.sha256"
    with open(checksum_file, 'w', encoding='utf-8') as f:
        f.write(f"{checksum}  {filename}\n")

    logger.info(f"Saved {len(all_prs)} PRs to {file_path} with checksum {checksum[:16]}...")
    return all_prs

def save_prs_to_raw(
    all_prs: List[Dict[str, Any]],
    output_dir: Path,
    repo: str
) -> Path:
    """
    Saves a list of PRs to a raw JSON file and generates a checksum.
    This is a wrapper for the logic inside fetch_prs_from_repo if needed separately,
    but currently fetch_prs_from_repo handles the save internally to ensure atomicity.
    """
    # This function is kept for API compatibility if called externally,
    # but the primary flow is via fetch_prs_from_repo which saves immediately.
    # If called, it performs the same save logic.
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = int(time.time())
    safe_repo_name = repo.replace("/", "_")
    filename = f"{safe_repo_name}_prs_{timestamp}.json"
    file_path = output_dir / filename

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(all_prs, f, indent=2, ensure_ascii=False)

    checksum = calculate_checksum(file_path)
    checksum_file = output_dir / f"{filename}.sha256"
    with open(checksum_file, 'w', encoding='utf-8') as f:
        f.write(f"{checksum}  {filename}\n")

    logger.info(f"Saved {len(all_prs)} PRs to {file_path} with checksum {checksum[:16]}...")
    return file_path

def run_batch_fetch(
    max_prs_per_repo: int = 200,
    repos: Optional[List[str]] = None,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Runs the fetch process across the prioritized list of repositories.
    Stops early if the total count of LLM-like PRs (heuristic: bot/automated)
    is insufficient, though full fetch is required for T013.

    Args:
        max_prs_per_repo: Max PRs to fetch per repo.
        repos: List of repos to fetch from. Defaults to REPO_LIST.
        output_dir: Directory to save raw data. Defaults to data/raw/.

    Returns:
        Summary statistics of the fetch operation.
    """
    if repos is None:
        repos = REPO_LIST
    if output_dir is None:
        output_dir = Path("data/raw")

    set_global_seed(42) # T004
    results = {
        "total_repos": len(repos),
        "successful_repos": 0,
        "total_prs_fetched": 0,
        "files_created": []
    }

    for repo in repos:
        try:
            prs = fetch_prs_from_repo(repo, output_dir, max_prs_per_repo)
            results["successful_repos"] += 1
            results["total_prs_fetched"] += len(prs)
            results["files_created"].append(str((output_dir / f"{repo.replace('/', '_')}_prs_*.json")))
        except Exception as e:
            logger.error(f"Failed to fetch from {repo}: {e}")
            # Fail loudly as per constraints
            raise RuntimeError(f"Critical failure fetching from {repo}: {e}")

    logger.info(f"Batch fetch complete. Total PRs: {results['total_prs_fetched']}")
    return results

def main():
    """
    Entry point for the fetch pipeline.
    """
    logger.info("Starting GitHub PR Fetch Pipeline (T013)...")
    config_summary = get_config_summary()
    logger.info(f"Config Summary: {config_summary}")

    try:
        stats = run_batch_fetch()
        print(json.dumps(stats, indent=2))
        logger.info("Pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
