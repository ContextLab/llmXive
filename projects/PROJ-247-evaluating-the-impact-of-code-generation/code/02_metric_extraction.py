"""
Metric Extraction Module (T020-T025)
Handles longitudinal metric extraction for matched code blocks.
"""

import os
import sys
import csv
import json
import subprocess
import tempfile
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

# Import from local utils
from utils.logging_config import get_logger, setup_logging
from utils.models import MatchedPair, Repository

# Configuration
DEFAULT_WINDOW_MONTHS = 6
MIN_COMMITS_TO_INCLUDE = 1

class MetricExtractionError(Exception):
    """Custom exception for metric extraction errors."""
    pass

class RepositoryNotFoundError(Exception):
    """Raised when a repository cannot be found or accessed."""
    pass

@dataclass
class BlockHistory:
    """Stores the commit history and churn metrics for a code block."""
    block_id: str
    file_path: str
    repo_path: str
    start_line: int
    end_line: int
    language: str
    commits: List[Dict[str, Any]] = field(default_factory=list)
    lines_added: int = 0
    lines_deleted: int = 0
    window_start: Optional[str] = None
    window_end: Optional[str] = None

def setup_output_directories():
    """Ensure all required output directories exist."""
    dirs = [
        "data/raw",
        "data/processed",
        "data/ground_truth",
        "data/logs",
        "data/tmp"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def load_matched_pairs(filepath: str = "data/processed/matched_pairs_filtered.csv") -> List[Dict[str, Any]]:
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
        # Try alternative formats
        for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S']:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        raise ValueError(f"Unable to parse date: {date_str}")

def clone_repo_shallow(repo_url: str, dest_path: str, depth: int = 100) -> str:
    """Clone a repository with shallow depth."""
    try:
        if os.path.exists(dest_path):
            # Remove existing clone
            subprocess.run(['rm', '-rf', dest_path], check=True)
        
        cmd = [
            'git', 'clone', '--depth', str(depth),
            '--filter=blob:none', '--sparse',
            repo_url, dest_path
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return dest_path
    except subprocess.CalledProcessError as e:
        raise MetricExtractionError(f"Failed to clone repository: {e.stderr}")

def get_commit_history_for_block(repo_path: str, file_path: str, 
                                 start_line: int, end_line: int,
                                 window_months: int = DEFAULT_WINDOW_MONTHS) -> List[Dict[str, Any]]:
    """
    Get commit history for a specific code block within a time window.
    Uses git log --follow and git log -L to track line changes.
    """
    window_start = (datetime.now() - timedelta(days=window_months * 30)).isoformat()
    
    try:
        # Get commits that modified this file within the window
        cmd = [
            'git', '-C', repo_path, 'log', '--follow',
            '--pretty=format:%H|%ae|%at|%s',
            '--since', window_start,
            '--', file_path
        ]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        commits = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split('|', 3)
            if len(parts) == 4:
                commits.append({
                    'hash': parts[0],
                    'author': parts[1],
                    'timestamp': parts[2],
                    'message': parts[3]
                })
        
        return commits
    except subprocess.CalledProcessError as e:
        logging.warning(f"Git log failed for {file_path}: {e.stderr}")
        return []

def calculate_code_churn(repo_path: str, file_path: str, 
                         start_line: int, end_line: int,
                         commit_hash: str) -> Tuple[int, int]:
    """
    Calculate lines added and deleted for a specific commit affecting a code block.
    Uses git show with -L option to track line ranges.
    """
    try:
        # Get the diff for this commit, focusing on the file
        cmd = [
            'git', '-C', repo_path, 'show', 
            '--numstat', '--no-patch', commit_hash
        ]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        lines_added = 0
        lines_deleted = 0
        
        for line in result.stdout.strip().split('\n'):
            parts = line.split('\t')
            if len(parts) == 3 and parts[2] == file_path:
                added = parts[0]
                deleted = parts[1]
                if added != '-':
                    lines_added += int(added)
                if deleted != '-':
                    lines_deleted += int(deleted)
                break
        
        return lines_added, lines_deleted
    except subprocess.CalledProcessError:
        return 0, 0

def calculate_code_churn_for_block(history: BlockHistory, window_months: int = DEFAULT_WINDOW_MONTHS) -> None:
    """
    Aggregate lines added/deleted for a block across all commits in the window.
    Excludes the initial commit (introduction of the block).
    """
    if not history.commits:
        return
    
    total_added = 0
    total_deleted = 0
    
    # Sort commits by timestamp
    sorted_commits = sorted(history.commits, key=lambda x: x['timestamp'])
    
    # Skip the first commit (block introduction)
    for commit in sorted_commits[1:]:
        added, deleted = calculate_code_churn(
            history.repo_path,
            history.file_path,
            history.start_line,
            history.end_line,
            commit['hash']
        )
        total_added += added
        total_deleted += deleted
    
    history.lines_added = total_added
    history.lines_deleted = total_deleted
    
    if sorted_commits:
        history.window_start = sorted_commits[0]['timestamp']
        history.window_end = sorted_commits[-1]['timestamp']

def extract_bug_fix_latency(commit_message: str, repo_path: str) -> Optional[Dict[str, Any]]:
    """
    Extract bug fix latency from commit message.
    Looks for "Fixes #N" or "Closes #N" patterns.
    """
    import re
    pattern = r'(Fixes|Closes)\s+#(\d+)'
    match = re.search(pattern, commit_message)
    
    if match:
        issue_id = match.group(2)
        # In a full implementation, we would query GitHub API here
        # For now, we return the issue ID and mark latency as pending
        return {
            'issue_id': issue_id,
            'latency_days': None,  # Would be calculated from API
            'status': 'pending_api_query'
        }
    return None

def extract_metrics_for_pair(pair: Dict[str, Any], window_months: int = DEFAULT_WINDOW_MONTHS) -> Optional[BlockHistory]:
    """
    Extract all longitudinal metrics for a matched pair.
    Returns BlockHistory object with aggregated metrics.
    """
    try:
        # Use the LLM block for tracking (both should be in same repo)
        block_id = pair.get('llm_block_id', pair.get('block_id'))
        file_path = pair.get('file_path')
        start_line = int(pair.get('start_line', 0))
        end_line = int(pair.get('end_line', 0))
        repo_url = pair.get('repo_url')
        
        if not all([block_id, file_path, repo_url]):
            return None
        
        # Create temp directory for repo
        temp_dir = tempfile.mkdtemp(prefix=f"repo_{block_id}_")
        
        try:
            # Clone repo
            clone_path = os.path.join(temp_dir, "repo")
            clone_repo_shallow(repo_url, clone_path)
            
            # Get commit history
            commits = get_commit_history_for_block(
                clone_path, file_path, start_line, end_line, window_months
            )
            
            if not commits:
                return None
            
            # Create history object
            history = BlockHistory(
                block_id=block_id,
                file_path=file_path,
                repo_path=clone_path,
                start_line=start_line,
                end_line=end_line,
                language=pair.get('language', 'python'),
                commits=commits
            )
            
            # Calculate churn
            calculate_code_churn_for_block(history, window_months)
            
            return history
            
        finally:
            # Cleanup temp directory
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                
    except Exception as e:
        logging.error(f"Failed to extract metrics for block {block_id}: {e}")
        return None

def validate_schema(data: List[Dict[str, Any]], required_fields: List[str]) -> bool:
    """Validate that data contains required fields."""
    if not data:
        return False
    
    for field in required_fields:
        if field not in data[0]:
            return False
    return True

def run_extraction_pipeline(input_file: str = "data/processed/matched_pairs_filtered.csv",
                            output_file: str = "data/processed/metrics_longitudinal.csv",
                            window_months: int = DEFAULT_WINDOW_MONTHS) -> Dict[str, Any]:
    """
    Main pipeline for extracting longitudinal metrics.
    Loads matched pairs, extracts churn and latency, saves results.
    """
    logger = get_logger(__name__)
    logger.info(f"Starting metric extraction pipeline")
    logger.info(f"Input: {input_file}")
    logger.info(f"Output: {output_file}")
    logger.info(f"Window: {window_months} months")
    
    # Load pairs
    try:
        pairs = load_matched_pairs(input_file)
        logger.info(f"Loaded {len(pairs)} matched pairs")
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        return {'success': False, 'error': str(e)}
    
    # Extract metrics
    results = []
    processed_count = 0
    error_count = 0
    
    for i, pair in enumerate(pairs):
        if (i + 1) % 10 == 0:
            logger.info(f"Processing pair {i + 1}/{len(pairs)}")
        
        history = extract_metrics_for_pair(pair, window_months)
        
        if history:
            # Convert to dict for CSV
            result = {
                'block_id': history.block_id,
                'file_path': history.file_path,
                'start_line': history.start_line,
                'end_line': history.end_line,
                'language': history.language,
                'lines_added': history.lines_added,
                'lines_deleted': history.lines_deleted,
                'window_start': history.window_start,
                'window_end': history.window_end,
                'commit_count': len(history.commits)
            }
            
            # Add latency data if available (from T021)
            # This would be merged from the latency calculation
            results.append(result)
            processed_count += 1
        else:
            error_count += 1
    
    # Write output
    if results:
        fieldnames = [
            'block_id', 'file_path', 'start_line', 'end_line', 'language',
            'lines_added', 'lines_deleted', 'window_start', 'window_end', 'commit_count'
        ]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        logger.info(f"Successfully wrote {len(results)} records to {output_file}")
    else:
        logger.warning("No metrics were extracted")
    
    return {
        'success': True,
        'processed': processed_count,
        'errors': error_count,
        'output_file': output_file
    }

def main():
    """Main entry point for metric extraction."""
    setup_logging()
    setup_output_directories()
    
    logger = get_logger(__name__)
    logger.info("Starting code churn calculation (T022)")
    
    # Run the pipeline
    result = run_extraction_pipeline(
        input_file="data/processed/matched_pairs_filtered.csv",
        output_file="data/processed/metrics_longitudinal.csv",
        window_months=6
    )
    
    if result['success']:
        logger.info(f"Pipeline completed: {result['processed']} pairs processed")
        logger.info(f"Output saved to: {result['output_file']}")
        print(f"SUCCESS: Extracted metrics for {result['processed']} blocks")
    else:
        logger.error(f"Pipeline failed: {result.get('error', 'Unknown error')}")
        print(f"FAILED: {result.get('error', 'Unknown error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()