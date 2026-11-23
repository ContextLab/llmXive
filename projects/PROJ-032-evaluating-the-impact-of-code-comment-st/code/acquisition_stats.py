import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from utils import configure_logging

def count_valid_repos(data_raw_dir: str = "data/raw") -> int:
    """
    Count the number of directories in data_raw_dir that contain a .git folder.
    Returns the count of valid clones with git history.
    """
    raw_path = Path(data_raw_dir)
    if not raw_path.exists():
        logging.warning(f"Directory {data_raw_dir} does not exist. Returning 0 valid repos.")
        return 0

    valid_count = 0
    for item in raw_path.iterdir():
        if item.is_dir():
            git_dir = item / ".git"
            if git_dir.exists() and git_dir.is_dir():
                valid_count += 1
            else:
                # Check for .git file (worktree case) or empty dir
                if item.is_dir() and not list(item.glob("*")):
                    continue
                if not git_dir.exists():
                    logging.debug(f"Repo {item.name} has no .git directory. Excluded.")
    
    return valid_count

def estimate_excluded_count(candidates_file: str = "data/raw/candidates.json", valid_count: int = 0) -> int:
    """
    Estimate the number of excluded repos by comparing the total candidate list
    against the count of valid repos found on disk.
    """
    candidates_path = Path(candidates_file)
    if not candidates_path.exists():
        logging.warning(f"Candidates file {candidates_file} not found. Cannot estimate exclusions.")
        return 0
    
    try:
        with open(candidates_path, 'r', encoding='utf-8') as f:
            candidates = json.load(f)
        total_candidates = len(candidates) if isinstance(candidates, list) else 0
    except (json.JSONDecodeError, IOError) as e:
        logging.error(f"Failed to read candidates file: {e}")
        return 0

    excluded = total_candidates - valid_count
    return max(0, excluded)

def calculate_success_rate(valid_count: int, total_candidates: int) -> float:
    """
    Calculate the success rate as valid_count / total_candidates.
    Returns 0.0 if total_candidates is 0.
    """
    if total_candidates == 0:
        return 0.0
    return valid_count / total_candidates

def main():
    """
    Main entry point to generate acquisition_stats.json.
    Reads from data/raw/ and data/raw/candidates.json to compute stats.
    Outputs to logs/acquisition_stats.json.
    """
    # Setup logging
    logger = configure_logging(log_path="logs/pipeline.log")
    logger.info("Starting acquisition stats generation for T016.")

    data_raw_dir = "data/raw"
    candidates_file = "data/raw/candidates.json"
    output_file = "logs/acquisition_stats.json"

    # Ensure logs directory exists
    Path("logs").mkdir(parents=True, exist_ok=True)

    # 1. Count valid repos
    valid_count = count_valid_repos(data_raw_dir)
    logger.info(f"Found {valid_count} valid repositories with git history.")

    # 2. Estimate excluded count
    excluded_count = estimate_excluded_count(candidates_file, valid_count)
    logger.info(f"Estimated excluded repositories: {excluded_count}.")

    # 3. Calculate success rate
    # We need total candidates to calculate rate. If candidates file is missing, 
    # we might infer total from excluded + valid, but better to read candidates.
    candidates_path = Path(candidates_file)
    total_candidates = valid_count + excluded_count if candidates_path.exists() else 0
    
    # Re-read candidates to get exact total if file exists
    if candidates_path.exists():
        try:
            with open(candidates_path, 'r', encoding='utf-8') as f:
                candidates = json.load(f)
            total_candidates = len(candidates) if isinstance(candidates, list) else valid_count
        except Exception:
            pass

    success_rate = calculate_success_rate(valid_count, total_candidates)
    logger.info(f"Success rate: {success_rate:.4f} ({valid_count}/{total_candidates}).")

    # 4. Compile stats
    stats = {
        "total_candidates": total_candidates,
        "valid_clones": valid_count,
        "excluded_count": excluded_count,
        "success_rate": success_rate,
        "status": "completed"
    }

    # 5. Write output
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        logger.info(f"Successfully wrote acquisition stats to {output_file}")
    except IOError as e:
        logger.error(f"Failed to write stats file: {e}")
        raise

    return stats

if __name__ == "__main__":
    main()