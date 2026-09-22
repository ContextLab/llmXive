"""
Fetch GitHub PRs from prioritized repositories.

This module implements the data acquisition pipeline for Pull Requests (PRs).
It handles:
- Pagination of the GitHub API
- Exponential backoff for rate limits
- Saving raw JSON payloads to data/raw/
- Generating SHA-256 checksums for data integrity (Constitution Principle III)
- A watchdog timer to prevent CI timeouts

Dependencies:
- requests (pinned in requirements.txt)
- utils.config (for repo list and API settings)
- utils.logging (for structured logging)
- utils.checksum (for SHA-256 generation)
"""

import os
import time
import json
import hashlib
import signal
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Project-relative imports
from utils.config import get_repo_list, get_api_settings
from utils.logging import get_logger, setup_logging
from utils.checksum import calculate_checksum
from utils.seeds import set_global_seed

# Initialize logger
logger = get_logger(__name__)

# Global watchdog flag
watchdog_triggered = False

def watchdog_handler(signum, frame):
    """Signal handler for watchdog timer."""
    global watchdog_triggered
    watchdog_triggered = True
    logger.error("Watchdog timer triggered: execution time exceeded limit. Exiting gracefully.")
    sys.exit(1)

def setup_watchdog(timeout_seconds: int = 300):
    """
    Set up a watchdog timer to prevent CI timeouts.
    Only works on Unix-like systems (SIGALRM).
    """
    if hasattr(signal, 'SIGALRM'):
        signal.signal(signal.SIGALRM, watchdog_handler)
        signal.alarm(timeout_seconds)
        logger.info(f"Watchdog timer set to {timeout_seconds} seconds.")
    else:
        logger.warning("SIGALRM not available (Windows). Watchdog timer disabled.")

def calculate_checksum(file_path: Path) -> str:
    """
    Calculate SHA-256 checksum of a file.
    Delegates to utils.checksum.calculate_checksum.
    """
    return calculate_checksum(file_path)

def fetch_prs_from_repo(
    repo: str,
    max_prs: int = 200,
    api_token: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetch PRs from a single GitHub repository with pagination and backoff.

    Args:
        repo: Repository string in format 'owner/repo'
        max_prs: Maximum number of PRs to fetch
        api_token: GitHub API token (optional, for higher rate limits)

    Returns:
        List of PR data dictionaries.
    """
    import requests

    api_settings = get_api_settings()
    base_url = api_settings.get('base_url', 'https://api.github.com')
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'llmXive-Research-Pipeline'
    }

    if api_token:
        headers['Authorization'] = f'token {api_token}'

    url = f"{base_url}/repos/{repo}/pulls"
    params = {
        'state': 'all',
        'per_page': 100,
        'sort': 'created',
        'direction': 'desc'
    }

    all_prs = []
    page = 1
    retries = 0
    max_retries = 5
    backoff_factor = 2

    logger.info(f"Fetching PRs from {repo}...")

    while len(all_prs) < max_prs:
        if watchdog_triggered:
            break

        params['page'] = page
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 200:
                prs_page = response.json()
                if not prs_page:
                    logger.info(f"No more PRs found on page {page} for {repo}.")
                    break

                # Extract relevant fields to keep payload manageable but complete
                # We need full data for classification and metrics later
                processed_prs = []
                for pr in prs_page:
                    pr_data = {
                        'pr_id': pr['number'],
                        'repo': repo,
                        'title': pr.get('title', ''),
                        'state': pr.get('state', 'closed'),
                        'created_at': pr.get('created_at'),
                        'updated_at': pr.get('updated_at'),
                        'merged_at': pr.get('merged_at'),
                        'user': {
                            'login': pr['user']['login'],
                            'type': pr['user'].get('type', 'Unknown')
                        },
                        'body': pr.get('body', ''),
                        'additions': pr.get('additions', 0),
                        'deletions': pr.get('deletions', 0),
                        'changed_files': pr.get('changed_files', 0),
                        'comments': pr.get('comments', 0),
                        'review_comments': pr.get('review_comments', 0),
                        'merge_commit_sha': pr.get('merge_commit_sha'),
                        'diff_url': pr.get('diff_url'),
                        # We will fetch the full diff separately if needed,
                        # but for now we store the URL and basic metadata.
                        # Classification will use commit messages and user info.
                        # Metrics will use timestamps and counts.
                    }
                    processed_prs.append(pr_data)

                all_prs.extend(processed_prs)
                logger.info(f"Fetched page {page} ({len(processed_prs)} PRs) from {repo}. Total: {len(all_prs)}")
                page += 1
                retries = 0  # Reset retries on success

                if len(all_prs) >= max_prs:
                    logger.info(f"Reached max PRs ({max_prs}) for {repo}.")
                    break

            elif response.status_code == 403:
                # Rate limit or other access issue
                if 'rate limit' in response.text.lower():
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limit hit. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded for rate limit. Skipping {repo}.")
                        break
                    continue
                else:
                    logger.error(f"API error 403 for {repo}: {response.text}")
                    break
            else:
                logger.error(f"API error {response.status_code} for {repo}: {response.text}")
                break

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {repo} (page {page}): {e}")
            retries += 1
            if retries > max_retries:
                logger.error(f"Max retries ({max_retries}) exceeded. Skipping {repo}.")
                break
            wait_time = backoff_factor ** retries
            logger.info(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)

    return all_prs

def save_prs_to_raw(prs: List[Dict[str, Any]], repo: str, output_dir: Path) -> Path:
    """
    Save PRs to a raw JSON file with checksum.

    Args:
        prs: List of PR dictionaries
        repo: Repository name (for filename)
        output_dir: Directory to save the file

    Returns:
        Path to the saved file
    """
    # Sanitize repo name for filename
    safe_repo = repo.replace('/', '_')
    timestamp = int(time.time())
    filename = f"prs_{safe_repo}_{timestamp}.json"
    file_path = output_dir / filename

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write JSON
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(prs, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(prs)} PRs to {file_path}")

    # Calculate and save checksum
    checksum = calculate_checksum(file_path)
    checksum_file = file_path.with_suffix(file_path.suffix + '.sha256')
    with open(checksum_file, 'w', encoding='utf-8') as f:
        f.write(f"{checksum}  {file_path.name}\n")

    logger.info(f"Checksum saved to {checksum_file}: {checksum}")

    return file_path

def run_batch_fetch(
    repo_list: Optional[List[str]] = None,
    max_prs_per_repo: int = 200,
    output_dir: Optional[Path] = None,
    timeout_seconds: int = 300
) -> List[Path]:
    """
    Fetch PRs from a list of repositories.

    Args:
        repo_list: List of 'owner/repo' strings. If None, uses config.
        max_prs_per_repo: Max PRs to fetch from each repo.
        output_dir: Directory to save raw JSON files. Defaults to data/raw/.
        timeout_seconds: Watchdog timeout.

    Returns:
        List of paths to saved JSON files.
    """
    if repo_list is None:
        repo_list = get_repo_list()

    if output_dir is None:
        # Use project root relative path
        output_dir = Path("data/raw")

    # Set up watchdog
    setup_watchdog(timeout_seconds)

    saved_files = []
    api_token = get_api_settings().get('token')

    total_prs_fetched = 0

    for repo in repo_list:
        if watchdog_triggered:
            break

        logger.info(f"Processing repository: {repo}")
        prs = fetch_prs_from_repo(repo, max_prs=max_prs_per_repo, api_token=api_token)

        if not prs:
            logger.warning(f"No PRs fetched for {repo}. Skipping save.")
            continue

        file_path = save_prs_to_raw(prs, repo, output_dir)
        saved_files.append(file_path)
        total_prs_fetched += len(prs)

        # Check if we have enough total PRs (optional global limit)
        # The task says "up to 200 PRs" which could mean total or per repo.
        # Given the "batch processing structure" and "prioritized list",
        # we interpret it as fetching from the list until we have a good sample,
        # but the task description says "fetch up to 200 PRs from prioritized list".
        # To be safe and efficient, we'll stop if we hit 200 total.
        if total_prs_fetched >= 200:
            logger.info(f"Total PRs fetched ({total_prs_fetched}) reached target. Stopping.")
            break

    logger.info(f"Batch fetch complete. Saved {len(saved_files)} files, {total_prs_fetched} total PRs.")
    return saved_files

def main():
    """Main entry point for the fetch pipeline."""
    # Set random seeds for reproducibility (though not much randomness here)
    set_global_seed(42)

    # Setup logging
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(log_file=log_dir / "fetch_github.log", level="INFO")

    logger.info("Starting GitHub PR fetch pipeline...")

    try:
        saved_files = run_batch_fetch(
            max_prs_per_repo=200,
            timeout_seconds=300
        )

        if not saved_files:
            logger.error("No files were saved. Check logs for errors.")
            sys.exit(1)

        logger.info(f"Pipeline successful. Output files: {saved_files}")

    except Exception as e:
        logger.exception(f"Pipeline failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
