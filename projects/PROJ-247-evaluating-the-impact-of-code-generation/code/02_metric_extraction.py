"""
Module: code/02_metric_extraction.py
Purpose: Extract longitudinal metrics (churn, latency) for matched code blocks.
Task: T025 - Save processed metrics to data/processed/metrics_longitudinal.csv with schema validation.
"""
import os
import sys
import csv
import json
import subprocess
import tempfile
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from sibling utils
from utils.models import MatchedPair
from utils.logging_config import get_logger

# Configure logger
logger = get_logger(__name__)

# Constants
DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"
LOGS_DIR = DATA_DIR / "logs"

# Schema definition for metrics_longitudinal.csv
METRICS_SCHEMA = {
    "pair_id": str,
    "repo_id": str,
    "block_id": str,
    "label": str,  # 'LLM' or 'Human'
    "churn_lines_added": int,
    "churn_lines_deleted": int,
    "churn_total_changes": int,
    "latency_days_to_fix": Optional[int],
    "num_commits": int,
    "window_start": str,
    "window_end": str,
    "extraction_timestamp": str
}

class MetricExtractionError(Exception):
    """Custom exception for metric extraction errors."""
    pass

class RepositoryNotFoundError(Exception):
    """Custom exception for repository not found errors."""
    pass

class BlockHistory:
    """Represents the history of a specific code block."""
    def __init__(self, repo_path: str, file_path: str, start_line: int, end_line: int):
        self.repo_path = repo_path
        self.file_path = file_path
        self.start_line = start_line
        self.end_line = end_line
        self.commits = []

    def add_commit(self, commit_hash: str, date: datetime, added: int, deleted: int, msg: str):
        self.commits.append({
            "hash": commit_hash,
            "date": date,
            "added": added,
            "deleted": deleted,
            "message": msg
        })

def setup_output_directories():
    """Ensure output directories exist."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

def load_matched_pairs(filepath: str) -> List[Dict[str, Any]]:
    """Load matched pairs from CSV."""
    pairs = []
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Matched pairs file not found: {filepath}")
    
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
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
        return datetime.strptime(date_str, "%Y-%m-%d")

def clone_repo_shallow(repo_url: str, dest_dir: str, depth: int = 100):
    """Perform a shallow clone of a repository."""
    try:
        subprocess.run(
            ["git", "clone", "--depth", str(depth), "--no-checkout", repo_url, dest_dir],
            check=True,
            capture_output=True,
            timeout=300
        )
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Git clone failed for {repo_url}: {e.stderr.decode()}")
        return False
    except subprocess.TimeoutExpired:
        logger.error(f"Git clone timed out for {repo_url}")
        return False

def get_commit_history_for_block(repo_path: str, file_path: str, start_line: int, end_line: int, since: datetime, until: datetime) -> List[Dict]:
    """
    Retrieve commit history affecting a specific line range in a file.
    Uses git log -L to track line changes.
    """
    # Format dates for git
    since_str = since.strftime("%Y-%m-%d")
    until_str = until.strftime("%Y-%m-%d")
    
    try:
        # git log -L :start,end:file --since --until --format
        cmd = [
            "git", "-C", repo_path,
            "log",
            f"--since={since_str}",
            f"--until={until_str}",
            f"-L:{start_line},{end_line}:{file_path}",
            "--format=%H|%ai|%s",
            "--numstat"
        ]
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=60)
        output = result.stdout
        
        commits = []
        # Parse output (simplified logic for demonstration; real implementation would be more robust)
        # The -L output is complex; we will parse the numstat and commit headers
        lines = output.split('\n')
        current_hash = None
        current_date = None
        current_msg = None
        current_added = 0
        current_deleted = 0
        
        for line in lines:
            if '|' in line and not line.startswith('\t'):
                # Commit header: hash|date|message
                parts = line.split('|', 2)
                if len(parts) == 3:
                    current_hash = parts[0]
                    current_date = parse_date(parts[1])
                    current_msg = parts[2]
                    current_added = 0
                    current_deleted = 0
            elif line.startswith('\t'):
                # Numstat line: added<tab>deleted<tab>file
                parts = line.split('\t')
                if len(parts) >= 3:
                    try:
                        added = int(parts[0]) if parts[0] != '-' else 0
                        deleted = int(parts[1]) if parts[1] != '-' else 0
                        # Only count if it matches our file path
                        if parts[2] == file_path:
                            current_added += added
                            current_deleted += deleted
                    except ValueError:
                        pass
            
            if current_hash and (line == '' or (current_hash and not line.startswith('\t') and '|' not in line)):
                # End of commit block (simplified)
                if current_added > 0 or current_deleted > 0:
                    commits.append({
                        "hash": current_hash,
                        "date": current_date,
                        "added": current_added,
                        "deleted": current_deleted,
                        "message": current_msg
                    })
        
        return commits
    except subprocess.CalledProcessError as e:
        logger.warning(f"Git log failed for {file_path}: {e.stderr.decode()}")
        return []
    except subprocess.TimeoutExpired:
        logger.warning(f"Git log timed out for {file_path}")
        return []

def extract_metrics_for_pair(pair: Dict[str, Any], repo_cache: Dict[str, str]) -> Dict[str, Any]:
    """
    Extract longitudinal metrics for a single matched pair.
    Returns a dictionary conforming to METRICS_SCHEMA.
    """
    repo_id = pair.get('repo_id')
    block_id = pair.get('block_id')
    label = pair.get('label')
    file_path = pair.get('file_path')
    start_line = int(pair.get('start_line', 0))
    end_line = int(pair.get('end_line', 0))
    window_start_str = pair.get('window_start')
    window_end_str = pair.get('window_end')
    
    if not window_start_str or not window_end_str:
        # Default window if not specified
        now = datetime.now()
        window_start = now.replace(month=now.month - 6 if now.month > 6 else now.month - 12 + 6)
        window_end = now
        window_start_str = window_start.isoformat()
        window_end_str = window_end.isoformat()
    
    window_start = parse_date(window_start_str)
    window_end = parse_date(window_end_str)
    
    # Clone or retrieve repo
    if repo_id not in repo_cache:
        # Assume repo_url is in the pair or we need to fetch it from metadata
        # For this task, we assume a mapping or that the repo was already cloned in T011
        # We will look for a local clone path based on repo_id
        repo_path = f"data/raw/repos/{repo_id}"
        if os.path.exists(repo_path):
            repo_cache[repo_id] = repo_path
        else:
            # Try to fetch URL from metadata if available
            logger.warning(f"Repo {repo_id} not found in cache. Skipping.")
            return None
    else:
        repo_path = repo_cache[repo_id]
    
    # Get commit history
    commits = get_commit_history_for_block(repo_path, file_path, start_line, end_line, window_start, window_end)
    
    # Calculate metrics
    total_added = sum(c['added'] for c in commits)
    total_deleted = sum(c['deleted'] for c in commits)
    total_changes = total_added + total_deleted
    
    # Calculate latency (simplified: find first commit with "Fix" or "Bug" in message)
    latency_days = None
    for c in commits:
        msg_lower = c['message'].lower()
        if "fix" in msg_lower or "bug" in msg_lower or "patch" in msg_lower:
            # Calculate days from window start
            delta = c['date'] - window_start
            latency_days = delta.days
            break
    
    return {
        "pair_id": pair.get('pair_id'),
        "repo_id": repo_id,
        "block_id": block_id,
        "label": label,
        "churn_lines_added": total_added,
        "churn_lines_deleted": total_deleted,
        "churn_total_changes": total_changes,
        "latency_days_to_fix": latency_days,
        "num_commits": len(commits),
        "window_start": window_start_str,
        "window_end": window_end_str,
        "extraction_timestamp": datetime.now().isoformat()
    }

def validate_schema(record: Dict[str, Any]) -> bool:
    """Validate a record against METRICS_SCHEMA."""
    for key, expected_type in METRICS_SCHEMA.items():
        if key not in record:
            logger.error(f"Missing key {key} in record")
            return False
        if expected_type == Optional[int]:
            if record[key] is not None and not isinstance(record[key], int):
                logger.error(f"Invalid type for {key}: expected int or None, got {type(record[key])}")
                return False
        else:
            if not isinstance(record[key], expected_type):
                logger.error(f"Invalid type for {key}: expected {expected_type}, got {type(record[key])}")
                return False
    return True

def run_extraction_pipeline():
    """Main pipeline to extract metrics and save to CSV."""
    setup_output_directories()
    
    input_file = PROCESSED_DIR / "matched_pairs.csv"
    output_file = PROCESSED_DIR / "metrics_longitudinal.csv"
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    logger.info(f"Loading matched pairs from {input_file}")
    pairs = load_matched_pairs(str(input_file))
    logger.info(f"Loaded {len(pairs)} pairs")
    
    repo_cache = {}
    results = []
    
    for i, pair in enumerate(pairs):
        logger.info(f"Processing pair {i+1}/{len(pairs)}: {pair.get('pair_id')}")
        try:
            metrics = extract_metrics_for_pair(pair, repo_cache)
            if metrics:
                if validate_schema(metrics):
                    results.append(metrics)
                else:
                    logger.warning(f"Validation failed for pair {pair.get('pair_id')}, skipping.")
            else:
                logger.warning(f"No metrics extracted for pair {pair.get('pair_id')}.")
        except Exception as e:
            logger.error(f"Error processing pair {pair.get('pair_id')}: {e}", exc_info=True)
            continue
    
    # Write to CSV
    logger.info(f"Writing {len(results)} results to {output_file}")
    fieldnames = list(METRICS_SCHEMA.keys())
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Pipeline complete. Output saved to {output_file}")
    return output_file

def main():
    """Entry point for the script."""
    try:
        run_extraction_pipeline()
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
