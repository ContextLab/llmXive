import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

from utils import configure_logging

def count_valid_repos(data_dir: str = "data/raw") -> int:
    """
    Count the number of valid repositories in the data/raw directory.
    A valid repo is defined as a directory containing a .git folder.
    """
    raw_dir = Path(data_dir)
    if not raw_dir.exists():
        return 0

    count = 0
    for item in raw_dir.iterdir():
        if item.is_dir() and (item / ".git").exists():
            count += 1
    return count

def estimate_excluded_count(candidates_file: str = "data/raw/candidates.json", valid_count: int = 0) -> int:
    """
    Estimate the number of excluded repos by comparing total candidates to valid clones.
    If the candidates file doesn't exist, return 0.
    """
    candidates_path = Path(candidates_file)
    if not candidates_path.exists():
        return 0

    try:
        with open(candidates_path, 'r', encoding='utf-8') as f:
            candidates = json.load(f)
        total_candidates = len(candidates)
        return max(0, total_candidates - valid_count)
    except (json.JSONDecodeError, TypeError):
        return 0

def calculate_success_rate(valid_count: int, total_candidates: int) -> float:
    """
    Calculate the success rate of cloning.
    Returns 0.0 if total_candidates is 0 to avoid division by zero.
    """
    if total_candidates == 0:
        return 0.0
    return valid_count / total_candidates

def main():
    """
    Main entry point to generate acquisition statistics.
    Reads candidates, counts valid repos, and writes stats to logs/acquisition_stats.json.
    """
    # Configure logging
    logger = configure_logging(log_path="logs/pipeline.log")
    logger.info("Starting acquisition stats generation (T016).")

    # Define paths
    data_dir = "data/raw"
    candidates_file = "data/raw/candidates.json"
    output_file = "logs/acquisition_stats.json"

    # Ensure logs directory exists
    Path("logs").mkdir(parents=True, exist_ok=True)

    # Gather metrics
    valid_count = count_valid_repos(data_dir)
    
    # We need the total candidates to calculate exclusions and success rate.
    # If the candidates file exists, we use it. Otherwise, we assume the valid count
    # is the total (since we have no list of failures) or 0 if no valid repos found.
    try:
        with open(candidates_file, 'r', encoding='utf-8') as f:
            candidates = json.load(f)
        total_candidates = len(candidates)
    except (FileNotFoundError, json.JSONDecodeError):
        logger.warning(f"Candidates file not found or invalid at {candidates_file}. Assuming total candidates = valid count.")
        total_candidates = valid_count

    excluded_count = max(0, total_candidates - valid_count)
    success_rate = calculate_success_rate(valid_count, total_candidates)

    stats = {
        "total_candidates": total_candidates,
        "valid_clones": valid_count,
        "excluded_repos": excluded_count,
        "success_rate": round(success_rate, 4)
    }

    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)

    logger.info(f"Acquisition stats written to {output_file}: {stats}")
    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    main()