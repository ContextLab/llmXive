import os
import csv
import random
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

from utils import configure_logging

# Configure logging
logger = configure_logging(log_path="logs/manual_labels.log")

def get_repos_with_git_history(base_dir: str) -> List[Path]:
    """
    Scan the base directory for cloned repositories that have a valid .git folder.
    Returns a list of Path objects pointing to the repo roots.
    """
    base_path = Path(base_dir)
    if not base_path.exists():
        logger.error(f"Base directory {base_dir} does not exist.")
        return []

    repos = []
    for item in base_path.iterdir():
        if item.is_dir() and (item / ".git").exists():
            repos.append(item)
    
    logger.info(f"Found {len(repos)} repositories with valid git history in {base_dir}")
    return repos

def get_commits_for_repo(repo_path: Path, n_samples: int = 20) -> List[str]:
    """
    Retrieve a list of commit hashes for a given repository.
    Uses 'git log' to fetch commits.
    """
    try:
        result = subprocess.run(
            ["git", "log", "--pretty=format:%H", "-n", str(n_samples * 2)],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            check=True
        )
        commits = result.stdout.strip().split('\n')
        # Deduplicate just in case
        commits = list(dict.fromkeys(commits))
        return commits[:n_samples]
    except subprocess.CalledProcessError as e:
        logger.warning(f"Failed to get commits for {repo_path}: {e}")
        return []

def is_bug_fix_heuristic(commit_msg: str) -> bool:
    """
    Heuristic to determine if a commit is a bug fix based on message content.
    This is used as a proxy for 'manual' labeling in an automated pipeline.
    """
    if not commit_msg:
        return False
    
    msg_lower = commit_msg.lower()
    bug_indicators = [
        "fix", "bug", "issue", "crash", "error", "exception", 
        "patch", "resolve", "correct", "repair"
    ]
    
    for indicator in bug_indicators:
        if indicator in msg_lower:
            return True
    return False

def stratified_sample_commits(repos: List[Path], total_target: int = 50) -> List[Tuple[str, str, str]]:
    """
    Perform stratified sampling of commits across repositories.
    Returns a list of tuples: (repo_id, commit_hash, label).
    """
    samples_per_repo = max(1, total_target // len(repos)) if repos else 0
    all_samples = []
    
    # We need to fetch the commit message to apply the heuristic
    # We will sample more initially and then filter/adjust if needed
    # But for simplicity, we sample N per repo, label them, and take the first T total.
    
    for repo_path in repos:
        repo_id = repo_path.name
        commits = get_commits_for_repo(repo_path, n_samples=samples_per_repo + 5)
        
        for commit in commits:
            try:
                # Get commit message
                msg_result = subprocess.run(
                    ["git", "log", "-1", "--pretty=%B", commit],
                    cwd=str(repo_path),
                    capture_output=True,
                    text=True,
                    check=True
                )
                msg = msg_result.stdout.strip().split('\n')[0] # First line
                label = "bug_fix" if is_bug_fix_heuristic(msg) else "not_bug_fix"
                all_samples.append((repo_id, commit, label))
            except subprocess.CalledProcessError:
                continue
        
        if len(all_samples) >= total_target:
            break
    
    # Shuffle to mix repos and labels
    random.shuffle(all_samples)
    return all_samples[:total_target]

def generate_labels(base_dir: str, output_path: str, target_count: int = 50):
    """
    Main function to generate the manual_labels.csv file.
    1. Finds repos.
    2. Samples commits.
    3. Applies heuristic labeling.
    4. Saves to CSV.
    """
    repos = get_repos_with_git_history(base_dir)
    if not repos:
        logger.error("No repositories found to sample from.")
        return

    logger.info(f"Starting stratified sampling for {target_count} labels...")
    samples = stratified_sample_commits(repos, total_target=target_count)
    
    if not samples:
        logger.error("No samples could be generated.")
        return

    # Ensure output directory exists
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["repo_id", "commit_hash", "label", "reason"])
        
        for repo_id, commit, label in samples:
            # Reason is derived from the heuristic check
            reason = "heuristic_bug_fix" if label == "bug_fix" else "heuristic_non_bug"
            writer.writerow([repo_id, commit, label, reason])
    
    logger.info(f"Successfully generated {len(samples)} labels at {output_path}")

def save_labels(samples: List[Tuple[str, str, str]], output_path: str):
    """
    Helper to save pre-computed samples to CSV.
    """
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["repo_id", "commit_hash", "label", "reason"])
        for repo_id, commit, label in samples:
            reason = "heuristic_bug_fix" if label == "bug_fix" else "heuristic_non_bug"
            writer.writerow([repo_id, commit, label, reason])

def main():
    """
    Entry point for the script.
    """
    logger.info("Starting Manual Labels Generation Pipeline")
    
    # Configuration
    raw_data_dir = "data/raw"
    output_file = "data/manual_labels.csv"
    target_samples = 50
    
    generate_labels(raw_data_dir, output_file, target_samples)
    logger.info("Manual Labels Generation Pipeline Complete")

if __name__ == "__main__":
    main()
