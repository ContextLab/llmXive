"""
Module to generate manual labels for bug fix detection.
This script creates data/manual_labels.csv by stratified sampling commits
from available repositories and labeling them based on commit message heuristics.
"""
import os
import csv
import random
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple, Optional

from utils import configure_logging

# Setup logging
logger = configure_logging(log_path="logs/manual_labels_generator.log")

# Heuristic keywords for bug fix detection
BUG_FIX_KEYWORDS = [
    'fix', 'bug', 'issue', 'error', 'patch', 'hotfix', 'resolve',
    'crash', 'failure', 'exception', 'defect', 'correct', 'repair'
]

NOT_BUG_KEYWORDS = [
    'feat', 'feature', 'add', 'new', 'enhance', 'improve', 'refactor',
    'docs', 'documentation', 'style', 'format', 'test', 'chore', 'build'
]

def get_repos_with_git_history() -> List[Path]:
    """
    Scan data/raw/ for directories that contain a .git folder.
    Returns a list of Path objects pointing to valid repositories.
    """
    raw_data_dir = Path("data/raw")
    if not raw_data_dir.exists():
        logger.warning(f"Directory {raw_data_dir} does not exist. No repos found.")
        return []

    repos = []
    for item in raw_data_dir.iterdir():
        if item.is_dir() and (item / ".git").exists():
            repos.append(item)

    logger.info(f"Found {len(repos)} repositories with git history in {raw_data_dir}")
    return repos

def get_commits_for_repo(repo_path: Path, max_commits: int = 100) -> List[Dict]:
    """
    Retrieve commit hashes and messages from a repository.
    Returns a list of dicts with 'hash' and 'message' keys.
    """
    try:
        # Get commit hash and subject line
        cmd = [
            "git", "-C", str(repo_path), "log",
            "--pretty=format:%H|%s",
            "-n", str(max_commits)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        commits = []
        for line in result.stdout.splitlines():
            if '|' in line:
                parts = line.split('|', 1)
                if len(parts) == 2:
                    commits.append({
                        'hash': parts[0],
                        'message': parts[1]
                    })
        
        logger.debug(f"Retrieved {len(commits)} commits from {repo_path.name}")
        return commits
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get commits from {repo_path}: {e}")
        return []

def is_bug_fix_heuristic(message: str) -> Tuple[bool, str]:
    """
    Determine if a commit is likely a bug fix based on message content.
    Returns (is_bug_fix, label_source).
    """
    msg_lower = message.lower()
    
    # Check for explicit bug fix indicators
    for keyword in BUG_FIX_KEYWORDS:
        if keyword in msg_lower:
            # Ensure it's not negated (simple check)
            if 'not ' + keyword not in msg_lower:
                return True, "keyword_match"
    
    # Check for feature/enhancement indicators to explicitly mark as not bug fix
    for keyword in NOT_BUG_KEYWORDS:
        if keyword in msg_lower:
            # Common prefixes for these keywords
            if msg_lower.startswith(keyword) or msg_lower.startswith(f"{keyword}:"):
                return False, "feature_keyword"
    
    # Default to not a bug fix if no clear indicators
    return False, "default"

def stratified_sample_commits(
    all_commits: List[Dict], 
    sample_size: int = 50, 
    seed: int = 42
) -> List[Dict]:
    """
    Perform stratified sampling on commits based on their heuristic label.
    Ensures a representative mix of bug_fix and not_bug_fix commits.
    """
    random.seed(seed)
    
    # Classify all commits first
    classified = []
    for commit in all_commits:
        is_bug, _ = is_bug_fix_heuristic(commit['message'])
        classified.append({
            **commit,
            'is_bug': is_bug
        })
    
    # Separate by class
    bug_fixes = [c for c in classified if c['is_bug']]
    not_bug_fixes = [c for c in classified if not c['is_bug']]
    
    logger.info(f"Initial pool: {len(bug_fixes)} bug fixes, {len(not_bug_fixes)} not bug fixes")
    
    # Calculate sample sizes proportionally
    total = len(classified)
    if total == 0:
        return []
    
    # Ensure we don't sample more than available
    n_bug = min(int(sample_size * len(bug_fixes) / total), len(bug_fixes))
    n_not_bug = sample_size - n_bug
    
    # Adjust if n_not_bug exceeds available
    if n_not_bug > len(not_bug_fixes):
        n_not_bug = len(not_bug_fixes)
        n_bug = min(sample_size - n_not_bug, len(bug_fixes))
    
    # Sample from each group
    sampled_bug = random.sample(bug_fixes, n_bug) if n_bug > 0 else []
    sampled_not_bug = random.sample(not_bug_fixes, n_not_bug) if n_not_bug > 0 else []
    
    sampled = sampled_bug + sampled_not_bug
    random.shuffle(sampled)
    
    logger.info(f"Sampled {len(sampled)} commits: {len(sampled_bug)} bug fixes, {len(sampled_not_bug)} not bug fixes")
    return sampled

def generate_labels(repos: List[Path], target_sample_size: int = 50) -> List[Dict]:
    """
    Generate labeled dataset from all repositories.
    Collects commits, applies heuristic, and performs stratified sampling.
    """
    all_commits = []
    
    for repo in repos:
        commits = get_commits_for_repo(repo)
        for commit in commits:
            commit['repo_id'] = repo.name
            all_commits.append(commit)
    
    if len(all_commits) == 0:
        logger.error("No commits found across all repositories.")
        return []
    
    logger.info(f"Total commits collected: {len(all_commits)}")
    
    # Perform stratified sampling
    sampled_commits = stratified_sample_commits(all_commits, target_sample_size)
    
    # Generate final labels
    labeled_data = []
    for commit in sampled_commits:
        is_bug, source = is_bug_fix_heuristic(commit['message'])
        labeled_data.append({
            'repo_id': commit['repo_id'],
            'commit_hash': commit['hash'],
            'commit_message': commit['message'],
            'label': 'bug_fix' if is_bug else 'not_bug_fix',
            'label_source': source
        })
    
    return labeled_data

def save_labels(labeled_data: List[Dict], output_path: str = "data/manual_labels.csv") -> None:
    """
    Save labeled data to CSV file.
    """
    if not labeled_data:
        logger.warning("No data to save.")
        return
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['repo_id', 'commit_hash', 'commit_message', 'label', 'label_source']
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(labeled_data)
    
    logger.info(f"Saved {len(labeled_data)} labeled commits to {output_path}")

def main():
    """
    Main entry point for generating manual labels.
    """
    logger.info("Starting manual label generation...")
    
    # Get repositories
    repos = get_repos_with_git_history()
    if not repos:
        logger.error("No repositories found. Aborting.")
        return
    
    # Generate labels
    labeled_data = generate_labels(repos, target_sample_size=50)
    
    if not labeled_data:
        logger.error("Failed to generate any labels.")
        return
    
    # Save to CSV
    save_labels(labeled_data)
    
    logger.info("Manual label generation completed successfully.")

if __name__ == "__main__":
    main()
