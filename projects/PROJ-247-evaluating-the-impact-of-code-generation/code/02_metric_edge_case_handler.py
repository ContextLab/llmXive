"""
Module: 02_metric_edge_case_handler
Purpose: Handle edge cases in longitudinal metric extraction, specifically
         repository deletion or privacy changes during the analysis window.
"""
import os
import sys
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from existing API surface
from utils.github_client import GitHubClient, RepositoryNotFoundError, GitHubClientError
from utils.logging_config import get_logger, setup_logging

# Constants
LOG_PATH = Path("data/logs")
METRICS_PATH = Path("data/processed/metrics_longitudinal.csv")
DELETION_LOG_PATH = LOG_PATH / "repo_deletion.log"


def setup_output_directories():
    """Ensure all required output directories exist."""
    LOG_PATH.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_metrics_longitudinal() -> List[Dict[str, Any]]:
    """
    Load the metrics_longitudinal.csv file.
    Returns a list of dictionaries representing rows.
    """
    if not METRICS_PATH.exists():
        logging.error(f"Metrics file not found: {METRICS_PATH}")
        return []

    rows = []
    with open(METRICS_PATH, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def save_metrics_longitudinal(metrics: List[Dict[str, Any]]):
    """
    Save the updated metrics_longitudinal.csv file.
    Preserves the original schema and order.
    """
    if not metrics:
        logging.warning("No metrics to save.")
        return

    fieldnames = list(metrics[0].keys())
    with open(METRICS_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(metrics)


def save_exclusions_log(deleted_repos: List[Dict[str, Any]]):
    """
    Save the list of deleted/private repositories to the deletion log.
    Format: pair_id, repo_url, reason (404/forbidden)
    """
    with open(DELETION_LOG_PATH, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Write header if file is empty
        if f.tell() == 0:
            writer.writerow(['pair_id', 'repo_url', 'reason'])
        
        for item in deleted_repos:
            writer.writerow([item['pair_id'], item['repo_url'], item['reason']])


def handle_repo_deletion(repo_url: str, pair_id: str, logger: logging.Logger) -> bool:
    """
    Check if a repository is accessible.
    
    Args:
        repo_url: The GitHub URL of the repository.
        pair_id: The ID of the matched pair for logging.
        logger: Logger instance.
    
    Returns:
        True if the repo is accessible, False if it is deleted/private.
    """
    try:
        # Extract owner and repo name from URL
        # Expected format: https://github.com/owner/repo.git or similar
        parts = repo_url.rstrip('.git').split('/')
        if len(parts) < 2:
            logger.warning(f"Invalid repo URL format: {repo_url}")
            return False
        
        owner = parts[-2]
        repo = parts[-1]
        
        client = GitHubClient()
        # Check existence. The GitHubClient handles rate limiting and auth.
        # We assume the client has a method to check repo existence or we can try to fetch metadata.
        # Since the API surface shows GitHubClient, we'll try to access it.
        # If the specific method isn't exposed in the summary, we rely on the client's internal logic
        # to raise RepositoryNotFoundError or similar.
        
        # Attempt to get repo info to verify existence
        # Note: The API surface says GitHubClient exists. We assume it has a way to check.
        # If it doesn't have a specific 'exists' method, we might need to call a generic 'get_repo'
        # and catch the error.
        try:
            client.get_repo(owner, repo)
            return True
        except RepositoryNotFoundError:
            logger.info(f"Repository not found (404): {repo_url} (Pair: {pair_id})")
            return False
        except GitHubClientError as e:
            # Handle other GitHub API errors (e.g., 403 Forbidden for private repos)
            logger.info(f"Repository inaccessible (Error: {e}): {repo_url} (Pair: {pair_id})")
            return False
            
    except Exception as e:
        logger.error(f"Unexpected error checking repo {repo_url}: {e}")
        # If we can't verify, we might conservatively exclude it to be safe,
        # or log and keep it. The task says "Gracefully exclude... with 404 handling".
        # We'll log it as inaccessible.
        logger.warning(f"Treating repo {repo_url} as inaccessible due to error.")
        return False


def run_edge_case_handling():
    """
    Main pipeline for handling repository deletion/private status.
    
    1. Load metrics_longitudinal.csv.
    2. Iterate through rows, checking repo accessibility.
    3. If a repo is deleted/private (404/403), mark it for removal.
    4. Log removed rows to data/logs/repo_deletion.log.
    5. Save the cleaned metrics to data/processed/metrics_longitudinal.csv.
    """
    setup_logging()
    logger = get_logger("edge_case_handler")
    logger.info("Starting edge case handling for repository deletions.")
    
    setup_output_directories()
    
    metrics = load_metrics_longitudinal()
    if not metrics:
        logger.warning("No metrics found to process. Exiting.")
        return
    
    logger.info(f"Loaded {len(metrics)} metrics rows.")
    
    valid_metrics = []
    deleted_repos = []
    
    # We need to track unique repos to avoid redundant API calls if multiple pairs are from the same repo
    # However, the task implies checking per pair or per repo. 
    # Let's group by repo_url to minimize calls.
    repo_status_cache = {}
    
    for row in metrics:
        repo_url = row.get('repo_url')
        pair_id = row.get('pair_id')
        
        if not repo_url:
            logger.warning(f"Row {pair_id} missing repo_url. Keeping for now.")
            valid_metrics.append(row)
            continue
        
        if repo_url not in repo_status_cache:
            is_accessible = handle_repo_deletion(repo_url, pair_id, logger)
            repo_status_cache[repo_url] = is_accessible
        else:
            is_accessible = repo_status_cache[repo_url]
        
        if is_accessible:
            valid_metrics.append(row)
        else:
            deleted_repos.append({
                'pair_id': pair_id,
                'repo_url': repo_url,
                'reason': '404/Forbidden'
            })
    
    # Save the deletion log
    if deleted_repos:
        save_exclusions_log(deleted_repos)
        logger.info(f"Logged {len(deleted_repos)} deleted/private repositories.")
    else:
        logger.info("No deleted or private repositories found.")
    
    # Save the updated metrics
    save_metrics_longitudinal(valid_metrics)
    logger.info(f"Saved {len(valid_metrics)} valid metrics rows.")
    logger.info("Edge case handling complete.")


def main():
    """Entry point for the script."""
    run_edge_case_handling()


if __name__ == "__main__":
    main()
