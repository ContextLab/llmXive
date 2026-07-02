"""
Task T016: Add logging for acquisition stats.

This script aggregates acquisition statistics from the cloning phase and
outputs them to logs/acquisition_stats.json. It calculates success rates,
counts excluded repositories, and totals valid clones.

It relies on the existence of `data/raw/` populated by `clone_batch` (T013)
and the logging configuration from `utils.configure_logging`.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from utils import configure_logging

def count_valid_repos(raw_dir: Path) -> int:
    """
    Count the number of directories in raw_dir that are valid git repositories.
    A valid repo is defined as a directory containing a 'git' directory (bare) 
    or having a valid .git folder (standard).
    """
    count = 0
    if not raw_dir.exists():
        return 0
    
    for item in raw_dir.iterdir():
        if item.is_dir():
            # Check for standard git repo (.git folder) or bare repo
            git_path = item / ".git"
            if git_path.exists() and git_path.is_dir():
                count += 1
            elif (item / "HEAD").exists() and (item / "refs").exists():
                # Likely a bare clone
                count += 1
    return count

def estimate_excluded_count(total_candidates: int, valid_count: int) -> int:
    """
    Estimates the number of excluded repositories based on the target candidate count
    and the number of valid clones found.
    """
    return max(0, total_candidates - valid_count)

def calculate_success_rate(valid_count: int, total_candidates: int) -> float:
    """
    Calculates the success rate of the acquisition process.
    """
    if total_candidates == 0:
        return 0.0
    return round((valid_count / total_candidates) * 100, 2)

def main():
    # Configure logging to capture execution info
    logger = configure_logging(log_path="logs/pipeline.log")
    logger.info("Starting acquisition stats aggregation (T016).")

    # Configuration
    project_root = Path.cwd()
    raw_data_dir = project_root / "data" / "raw"
    log_output_dir = project_root / "logs"
    output_file = log_output_dir / "acquisition_stats.json"

    # Ensure logs directory exists
    log_output_dir.mkdir(parents=True, exist_ok=True)

    # Parameters (These should ideally be passed or read from a state file,
    # but for this task we infer from the file system state and a fixed candidate target
    # as per the task description "Identify 500 high-star Python repos")
    target_candidates = 500 

    # Perform analysis
    valid_repos = count_valid_repos(raw_data_dir)
    excluded_repos = estimate_excluded_count(target_candidates, valid_repos)
    success_rate = calculate_success_rate(valid_repos, target_candidates)

    # Construct stats object
    stats: Dict[str, Any] = {
        "task_id": "T016",
        "timestamp": None, # Will be set by json dump if needed, or omitted for static stats
        "acquisition_summary": {
            "target_candidates": target_candidates,
            "valid_clones": valid_repos,
            "excluded_repos": excluded_repos,
            "success_rate_percent": success_rate
        },
        "status": "success" if valid_repos > 0 else "partial_failure",
        "details": {
            "raw_data_dir": str(raw_data_dir),
            "output_file": str(output_file)
        }
    }

    # Write to JSON
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2)
        logger.info(f"Acquisition stats written to {output_file}")
        logger.info(f"Valid clones: {valid_repos}, Excluded: {excluded_repos}, Rate: {success_rate}%")
    except IOError as e:
        logger.error(f"Failed to write acquisition stats: {e}")
        raise

    return stats

if __name__ == "__main__":
    main()
