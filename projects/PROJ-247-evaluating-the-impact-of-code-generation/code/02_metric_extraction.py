"""
Metric Extraction Module for Longitudinal Analysis.

Handles the extraction of code churn and bug fix latency metrics for matched pairs.
Includes edge case handling for null latencies and repository deletion.
"""
import os
import sys
import csv
import json
import subprocess
import tempfile
import logging
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

# Import from project utils
from utils.github_client import GitHubClient, GitHubClientError, RepositoryNotFoundError
from utils.logging_config import get_logger, setup_logging

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = DATA_DIR / "logs"
PROCESSED_DIR = DATA_DIR / "processed"

# Ensure directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

class MetricExtractionError(Exception):
    """Custom exception for metric extraction errors."""
    pass

class RepositoryNotFoundError(Exception):
    """Custom exception for missing repository errors."""
    pass

class BlockHistory:
    """Represents the history of a code block across commits."""
    def __init__(self, block_id: str, file_path: str, repo_path: str):
        self.block_id = block_id
        self.file_path = file_path
        self.repo_path = repo_path
        self.commits: List[Dict[str, Any]] = []
        self.churn_data: Dict[str, int] = {"added": 0, "deleted": 0}

def setup_output_directories():
    """Ensure all required output directories exist."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

def load_matched_pairs(filepath: str) -> List[Dict[str, Any]]:
    """Load matched pairs from CSV."""
    pairs = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pairs.append(row)
    return pairs

def parse_date(date_str: str) -> datetime:
    """Parse ISO format date string."""
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except ValueError:
        # Fallback for common formats
        return datetime.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S")

def clone_repo_shallow(repo_url: str, target_dir: Path, depth: int = 100):
    """Perform a shallow clone of a repository."""
    if target_dir.exists():
        return target_dir
    
    try:
        subprocess.run(
            ["git", "clone", "--depth", str(depth), repo_url, str(target_dir)],
            check=True,
            capture_output=True
        )
        return target_dir
    except subprocess.CalledProcessError as e:
        raise MetricExtractionError(f"Failed to clone repository: {e.stderr.decode()}")

def get_commit_history_for_block(repo_path: Path, file_path: str, since: datetime, until: datetime) -> List[Dict[str, Any]]:
    """Get commit history for a specific file within a time window."""
    try:
        # Format dates for git log
        since_str = since.isoformat()
        until_str = until.isoformat()
        
        cmd = [
            "git", "-C", str(repo_path),
            "log",
            f"--since={since_str}",
            f"--until={until_str}",
            "--pretty=format:%H|%ai|%s",
            "--name-status",
            "--", file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        
        commits = []
        current_commit = None
        
        for line in lines:
            if not line:
                continue
            if '|' in line and current_commit is None:
                # New commit header
                parts = line.split('|', 2)
                if len(parts) >= 3:
                    current_commit = {
                        "hash": parts[0],
                        "date": parse_date(parts[1]),
                        "message": parts[2],
                        "files": []
                    }
            elif current_commit and line.startswith('\t'):
                # File change line
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    current_commit["files"].append({
                        "status": parts[0],
                        "path": parts[1]
                    })
            elif current_commit and line == "":
                # End of commit block
                commits.append(current_commit)
                current_commit = None
        
        if current_commit:
            commits.append(current_commit)
            
        return commits
    except subprocess.CalledProcessError as e:
        # If file doesn't exist in history, return empty
        return []

def calculate_code_churn(commits: List[Dict[str, Any]], file_path: str) -> Tuple[int, int]:
    """Calculate lines added and deleted for a file across commits."""
    total_added = 0
    total_deleted = 0
    
    for commit in commits:
        for file_change in commit.get("files", []):
            if file_change["path"] == file_path:
                # In a real implementation, we would parse the diff to get exact line counts
                # For this task, we simulate based on the existence of the file change
                # In a full implementation, we'd use `git diff-tree` or `git show`
                # to get the actual diff stats
                pass
    
    # Actual implementation using git diff-tree for stats
    repo_path = commits[0]["repo_path"] if commits else None
    if not repo_path or not commits:
        return 0, 0
        
    for commit in commits:
        try:
            cmd = [
                "git", "-C", str(repo_path),
                "diff-tree", "--no-commit-id", "--numstat",
                commit["hash"], commit["hash"] + "^"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                parts = line.split('\t')
                if len(parts) >= 3 and parts[2] == file_path:
                    try:
                        added = int(parts[0]) if parts[0] != '-' else 0
                        deleted = int(parts[1]) if parts[1] != '-' else 0
                        total_added += added
                        total_deleted += deleted
                    except ValueError:
                        continue
        except Exception:
            continue
            
    return total_added, total_deleted

def extract_bug_fix_latency(commit: Dict[str, Any], github_client: Optional[GitHubClient] = None, owner: str = None, repo: str = None) -> Optional[Dict[str, Any]]:
    """
    Extract bug fix latency from a commit.
    Looks for 'Fixes #N' or 'Closes #N' patterns.
    """
    message = commit.get("message", "")
    pattern = r"(?:Fixes|Closes)\s+#(\d+)"
    match = re.search(pattern, message)
    
    if not match:
        return None
        
    issue_number = int(match.group(1))
    
    if not github_client or not owner or not repo:
        # Cannot verify without API access
        return {"issue_id": issue_number, "latency_days": None, "verified": False}
        
    try:
        # Fetch issue details
        issue = github_client.get_issue(owner, repo, issue_number)
        if not issue:
            return {"issue_id": issue_number, "latency_days": None, "verified": False}
            
        closed_at = issue.get("closed_at")
        if not closed_at:
            return {"issue_id": issue_number, "latency_days": None, "verified": False}
            
        commit_date = commit.get("date")
        if not commit_date:
            return {"issue_id": issue_number, "latency_days": None, "verified": False}
            
        # Calculate latency
        closed_dt = parse_date(closed_at)
        latency = (closed_dt - commit_date).days
        
        return {
            "issue_id": issue_number,
            "latency_days": latency,
            "verified": True
        }
    except (GitHubClientError, RepositoryNotFoundError, KeyError) as e:
        logging.warning(f"Could not verify issue #{issue_number}: {e}")
        return {"issue_id": issue_number, "latency_days": None, "verified": False}

def extract_metrics_for_pair(pair: Dict[str, Any], github_client: Optional[GitHubClient] = None) -> Dict[str, Any]:
    """Extract all metrics for a single matched pair."""
    block_id = pair.get("block_id")
    file_path = pair.get("file_path")
    repo_path = pair.get("repo_path")
    repo_owner = pair.get("repo_owner")
    repo_name = pair.get("repo_name")
    introduced_at = pair.get("introduced_at")
    
    if not all([block_id, file_path, repo_path, introduced_at]):
        return {
            "block_id": block_id,
            "latency_days": None,
            "issue_id": None,
            "lines_added": None,
            "lines_deleted": None,
            "window_start": None,
            "window_end": None,
            "latency_null": True,
            "churn_null": False
        }
    
    try:
        introduced_dt = parse_date(introduced_at)
        # Define a 90-day window for analysis
        window_end = introduced_dt + timedelta(days=90)
        
        # Get commit history
        commits = get_commit_history_for_block(
            Path(repo_path), file_path, introduced_dt, window_end
        )
        
        # Calculate churn
        lines_added, lines_deleted = calculate_code_churn(commits, file_path)
        
        # Try to extract latency from the first relevant commit (e.g., first fix commit)
        latency_result = None
        for commit in commits:
            lat = extract_bug_fix_latency(commit, github_client, repo_owner, repo_name)
            if lat and lat.get("latency_days") is not None:
                latency_result = lat
                break
            elif lat:
                latency_result = lat # Keep the best effort even if None
        
        if not latency_result:
            latency_result = {"issue_id": None, "latency_days": None, "verified": False}
        
        return {
            "block_id": block_id,
            "latency_days": latency_result.get("latency_days"),
            "issue_id": latency_result.get("issue_id"),
            "lines_added": lines_added,
            "lines_deleted": lines_deleted,
            "window_start": introduced_dt.isoformat(),
            "window_end": window_end.isoformat(),
            "latency_null": latency_result.get("latency_days") is None,
            "churn_null": False
        }
        
    except Exception as e:
        logging.error(f"Error extracting metrics for {block_id}: {e}")
        return {
            "block_id": block_id,
            "latency_days": None,
            "issue_id": None,
            "lines_added": None,
            "lines_deleted": None,
            "window_start": None,
            "window_end": None,
            "latency_null": True,
            "churn_null": True
        }

def validate_schema(row: Dict[str, Any]) -> bool:
    """Validate that a row has the required schema."""
    required = [
        "block_id", "latency_days", "issue_id", 
        "lines_added", "lines_deleted", 
        "window_start", "window_end"
    ]
    return all(k in row for k in required)

def run_extraction_pipeline():
    """Main pipeline execution."""
    setup_output_directories()
    logger = get_logger("metric_extraction")
    
    input_file = PROCESSED_DIR / "matched_pairs_filtered.csv"
    output_file = PROCESSED_DIR / "metrics_longitudinal.csv"
    latency_exclusions_log = LOGS_DIR / "latency_exclusions.log"
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Initialize GitHub client
    github_client = None
    token = os.getenv("GITHUB_TOKEN")
    if token:
        try:
            github_client = GitHubClient(token)
        except Exception as e:
            logger.warning(f"Could not initialize GitHub client: {e}. Latency verification will be limited.")
    
    pairs = load_matched_pairs(str(input_file))
    logger.info(f"Loaded {len(pairs)} matched pairs.")
    
    results = []
    exclusions = []
    
    for i, pair in enumerate(pairs):
        logger.info(f"Processing pair {i+1}/{len(pairs)}: {pair.get('block_id')}")
        metrics = extract_metrics_for_pair(pair, github_client)
        
        # Validate schema
        if not validate_schema(metrics):
            logger.warning(f"Invalid metrics for {metrics.get('block_id')}, skipping.")
            continue
            
        results.append(metrics)
        
        # Handle edge cases: Log null latency
        if metrics.get("latency_null"):
            reason = "No 'Fixes/Closes #N' pattern found in commit messages or issue verification failed"
            if metrics.get("issue_id"):
                reason = f"Issue #{metrics['issue_id']} not closed or not found"
            
            exclusions.append({
                "pair_id": metrics["block_id"],
                "reason": reason
            })
    
    # Write results
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            "block_id", "latency_days", "issue_id",
            "lines_added", "lines_deleted",
            "window_start", "window_end",
            "latency_null", "churn_null"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Wrote {len(results)} metrics to {output_file}")
    
    # Write exclusions log
    with open(latency_exclusions_log, 'w', encoding='utf-8') as f:
        f.write("pair_id,reason\n")
        for exc in exclusions:
            # Escape commas in reason for CSV safety
            reason = exc["reason"].replace('"', '""')
            if ',' in reason:
                reason = f'"{reason}"'
            f.write(f"{exc['pair_id']},{reason}\n")
    
    logger.info(f"Wrote {len(exclusions)} latency exclusions to {latency_exclusions_log}")
    
    return results

def main():
    """Entry point for the script."""
    try:
        run_extraction_pipeline()
        print("Metric extraction completed successfully.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()