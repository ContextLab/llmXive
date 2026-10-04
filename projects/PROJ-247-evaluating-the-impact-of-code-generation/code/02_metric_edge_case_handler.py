"""
Module: 02_metric_edge_case_handler.py
Purpose: Handle edge cases in metric extraction, specifically repo deletion/private status.
"""
import os
import sys
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import time

# Import existing utilities
from utils.github_client import GitHubClient, RepositoryNotFoundError, GitHubClientError
from utils.logging_config import get_logger

# Constants
LOG_PATH = Path("data/logs")
METRICS_PATH = Path("data/processed")
REPO_DELETION_LOG = LOG_PATH / "repo_deletion.log"
METRICS_OUTPUT = METRICS_PATH / "metrics_longitudinal.csv"

def setup_output_directories():
    """Ensure required directories exist."""
    LOG_PATH.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.mkdir(parents=True, exist_ok=True)

def load_metrics_longitudinal() -> List[Dict[str, Any]]:
    """Load metrics_longitudinal.csv if it exists."""
    if not METRICS_OUTPUT.exists():
        return []
    
    rows = []
    with open(METRICS_OUTPUT, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def save_metrics_longitudinal(metrics: List[Dict[str, Any]]):
    """Save updated metrics_longitudinal.csv."""
    if not metrics:
        # Write empty file with headers if no data
        fieldnames = ['block_id', 'latency_days', 'issue_id', 'lines_added', 'lines_deleted', 'window_start', 'window_end', 'repo_name']
        with open(METRICS_OUTPUT, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
        return

    # Determine fieldnames from first row
    fieldnames = list(metrics[0].keys())
    with open(METRICS_OUTPUT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(metrics)

def save_exclusions_log(log_path: Path, entries: List[Dict[str, str]]):
    """Save exclusion log entries."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'a', encoding='utf-8') as f:
        for entry in entries:
            # Format: repo_name, reason, timestamp
            line = f"{entry['repo_name']},{entry['reason']},{entry['timestamp']}\n"
            f.write(line)

def handle_repo_deletion(metrics: List[Dict[str, Any]], github_client: GitHubClient) -> List[Dict[str, Any]]:
    """
    Check if repos for each metric entry are still accessible.
    If a repo returns 404 (not found) or is private/deleted, exclude it from analysis.
    
    Args:
        metrics: List of metric dictionaries
        github_client: Initialized GitHubClient instance
    
    Returns:
        Filtered list of metrics excluding deleted/private repos
    """
    valid_metrics = []
    excluded_entries = []
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    # Group metrics by repo to minimize API calls
    repo_check_cache = {}
    
    for metric in metrics:
        repo_name = metric.get('repo_name')
        if not repo_name:
            # If repo_name is missing, we cannot verify, so keep for now (or exclude if strict)
            # For safety, we keep it but log a warning
            logging.warning(f"Missing repo_name for block_id {metric.get('block_id')}, keeping for manual review.")
            valid_metrics.append(metric)
            continue
        
        # Check cache first
        if repo_name in repo_check_cache:
            is_valid = repo_check_cache[repo_name]
        else:
            try:
                # Attempt to fetch repo metadata to verify existence
                # This will raise RepositoryNotFoundError if 404
                repo_info = github_client.get_repo_info(repo_name)
                is_valid = True
            except RepositoryNotFoundError:
                is_valid = False
                excluded_entries.append({
                    'repo_name': repo_name,
                    'reason': 'Repository not found (404) or deleted',
                    'timestamp': timestamp
                })
            except GitHubClientError as e:
                # Handle other GitHub errors (rate limit, auth, etc.)
                logging.error(f"GitHub API error for {repo_name}: {e}")
                # If we can't verify due to API error, we keep the data but log
                valid_metrics.append(metric)
                continue
        
        repo_check_cache[repo_name] = is_valid
        
        if is_valid:
            valid_metrics.append(metric)
        # else: excluded (already logged)
    
    # Save deletion log
    if excluded_entries:
        save_exclusions_log(REPO_DELETION_LOG, excluded_entries)
        logging.info(f"Excluded {len(excluded_entries)} entries due to repo deletion/private status. Log: {REPO_DELETION_LOG}")
    
    return valid_metrics

def run_edge_case_handling():
    """Main entry point for handling edge cases in metrics."""
    setup_output_directories()
    logger = get_logger(__name__)
    logger.info("Starting edge case handling for metric extraction (T024)...")
    
    # Initialize GitHub client
    try:
        github_client = GitHubClient()
    except Exception as e:
        logger.error(f"Failed to initialize GitHub client: {e}")
        # If we can't check repos, we proceed with existing data but log warning
        logger.warning("Proceeding without repo deletion check due to GitHub client initialization failure.")
        return
    
    # Load existing metrics
    metrics = load_metrics_longitudinal()
    logger.info(f"Loaded {len(metrics)} metric entries from {METRICS_OUTPUT}")
    
    if not metrics:
        logger.info("No metrics to process. Exiting.")
        return
    
    # Handle repo deletion
    valid_metrics = handle_repo_deletion(metrics, github_client)
    
    # Save updated metrics
    save_metrics_longitudinal(valid_metrics)
    logger.info(f"Saved {len(valid_metrics)} valid metric entries to {METRICS_OUTPUT}")
    
    deleted_count = len(metrics) - len(valid_metrics)
    if deleted_count > 0:
        logger.info(f"Removed {deleted_count} entries due to repo deletion/private status.")
    else:
        logger.info("No repos were deleted or private.")

def main():
    """CLI entry point."""
    run_edge_case_handling()

if __name__ == "__main__":
    main()
