"""
Extract review metrics from labeled PRs and join with complexity scores.

This module calculates:
- comment_count: Number of comments on the PR
- time_to_merge_minutes: Time from PR creation to merge in minutes
- review_cycles: Number of distinct review cycles (based on event timestamps)

It joins the labeled PRs with complexity scores to produce a unified dataset.
"""
import os
import csv
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import logging utilities
from utils.logging import get_logger, setup_logging
from utils.config import get_config_summary

logger = None

def setup_logging_and_config():
    """Initialize logging and load configuration."""
    global logger
    log_path = Path("data/logs")
    log_path.mkdir(parents=True, exist_ok=True)
    logger = setup_logging(
        name="extract_metrics",
        log_dir=log_path,
        level="INFO"
    )
    config = get_config_summary()
    logger.info(f"Configuration loaded: {config}")
    return config

def load_prs_labeled(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load labeled PRs from the processed CSV file.
    
    Args:
        input_path: Path to data/processed/prs_labeled.csv
        
    Returns:
        List of PR dictionaries with metadata and labels
        
    Raises:
        FileNotFoundError: If the input file doesn't exist
        ValueError: If required columns are missing
    """
    if not input_path.exists():
        logger.error(f"Labeled PRs file not found: {input_path}")
        raise FileNotFoundError(f"Labeled PRs file not found: {input_path}")
    
    prs = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        required_cols = {'pr_id', 'source_type', 'confidence_score'}
        if not required_cols.issubset(set(reader.fieldnames or [])):
            missing = required_cols - set(reader.fieldnames or [])
            raise ValueError(f"Missing required columns in {input_path}: {missing}")
        
        for row in reader:
            # Convert pr_id to int
            row['pr_id'] = int(row['pr_id'])
            prs.append(row)
    
    logger.info(f"Loaded {len(prs)} labeled PRs from {input_path}")
    return prs

def load_complexity_scores(input_path: Path) -> Dict[int, float]:
    """
    Load complexity scores from the processed CSV file.
    
    Args:
        input_path: Path to data/processed/complexity_scores.csv
        
    Returns:
        Dictionary mapping pr_id (int) to complexity_score (float)
        
    Raises:
        FileNotFoundError: If the input file doesn't exist
        ValueError: If required columns are missing
    """
    if not input_path.exists():
        logger.error(f"Complexity scores file not found: {input_path}")
        raise FileNotFoundError(f"Complexity scores file not found: {input_path}")
    
    scores = {}
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        required_cols = {'pr_id', 'complexity_score'}
        if not required_cols.issubset(set(reader.fieldnames or [])):
            missing = required_cols - set(reader.fieldnames or [])
            raise ValueError(f"Missing required columns in {input_path}: {missing}")
        
        for row in reader:
            pr_id = int(row['pr_id'])
            complexity_score = float(row['complexity_score'])
            scores[pr_id] = complexity_score
    
    logger.info(f"Loaded {len(scores)} complexity scores from {input_path}")
    return scores

def parse_timestamp(timestamp_str: str) -> datetime:
    """
    Parse ISO format timestamp string to datetime object.
    
    Args:
        timestamp_str: ISO format timestamp (e.g., '2024-01-15T10:30:00Z')
        
    Returns:
        datetime object
        
    Raises:
        ValueError: If timestamp format is invalid
    """
    # Handle various ISO formats
    timestamp_str = timestamp_str.replace('Z', '+00:00')
    try:
        return datetime.fromisoformat(timestamp_str)
    except ValueError:
        # Try alternative format
        try:
            return datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%f%z')
        except ValueError:
            raise ValueError(f"Unable to parse timestamp: {timestamp_str}")

def calculate_time_to_merge_minutes(created_at: str, merged_at: Optional[str]) -> Optional[float]:
    """
    Calculate time to merge in minutes.
    
    Args:
        created_at: PR creation timestamp
        merged_at: PR merge timestamp (may be None if not merged)
        
    Returns:
        Time to merge in minutes, or None if not merged
    """
    if merged_at is None or merged_at == '' or merged_at == 'null':
        return None
    
    created_dt = parse_timestamp(created_at)
    merged_dt = parse_timestamp(merged_at)
    
    delta = merged_dt - created_dt
    return delta.total_seconds() / 60.0

def calculate_review_cycles(events: List[Dict[str, Any]]) -> int:
    """
    Calculate number of review cycles based on events.
    
    A review cycle is counted when there's a sequence of:
    1. Code change (push/commit)
    2. Review comment or approval
    
    Args:
        events: List of PR events with timestamps and types
        
    Returns:
        Number of review cycles
    """
    if not events:
        return 0
    
    # Filter for relevant events
    relevant_events = []
    for event in events:
        event_type = event.get('type', '').lower()
        if 'review' in event_type or 'comment' in event_type or 'commit' in event_type:
            timestamp = event.get('created_at')
            if timestamp:
                try:
                    dt = parse_timestamp(timestamp)
                    relevant_events.append((dt, event_type))
                except ValueError:
                    continue
    
    if not relevant_events:
        return 0
    
    # Sort by timestamp
    relevant_events.sort(key=lambda x: x[0])
    
    # Count cycles: a cycle starts with a commit/change followed by a review
    cycles = 0
    last_was_change = False
    
    change_keywords = ['commit', 'push', 'changed']
    review_keywords = ['review', 'comment', 'approved', 'changes_requested']
    
    for _, event_type in relevant_events:
        is_change = any(kw in event_type for kw in change_keywords)
        is_review = any(kw in event_type for kw in review_keywords)
        
        if is_change:
            last_was_change = True
        elif is_review and last_was_change:
            cycles += 1
            last_was_change = False
    
    return cycles

def extract_comment_count(pr_data: Dict[str, Any]) -> int:
    """
    Extract comment count from PR data.
    
    Args:
        pr_data: PR dictionary with comments/issue_comments
        
    Returns:
        Number of comments
    """
    # Try multiple possible locations for comment data
    comment_count = 0
    
    # Check for comments field
    if 'comments' in pr_data:
        comments = pr_data['comments']
        if isinstance(comments, int):
            comment_count = comments
        elif isinstance(comments, list):
            comment_count = len(comments)
    
    # Check for issue_comments field (GitHub API often separates)
    if 'issue_comments' in pr_data:
        issue_comments = pr_data['issue_comments']
        if isinstance(issue_comments, list):
            # Add to existing count if already set
            comment_count += len(issue_comments)
    
    # Check for review_comments field
    if 'review_comments' in pr_data:
        review_comments = pr_data['review_comments']
        if isinstance(review_comments, int):
            comment_count += review_comments
        elif isinstance(review_comments, list):
            comment_count += len(review_comments)
    
    return comment_count

def extract_pr_metrics(pr: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract all metrics for a single PR.
    
    Args:
        pr: PR dictionary with full data
        
    Returns:
        Dictionary with pr_id, comment_count, time_to_merge_minutes, review_cycles
    """
    pr_id = pr.get('pr_id')
    
    # Extract comment count
    comment_count = extract_comment_count(pr)
    
    # Extract time to merge
    created_at = pr.get('created_at')
    merged_at = pr.get('merged_at')
    time_to_merge = None
    if created_at:
        time_to_merge = calculate_time_to_merge_minutes(created_at, merged_at)
    
    # Extract review cycles
    events = pr.get('events', pr.get('timeline', []))
    review_cycles = calculate_review_cycles(events)
    
    return {
        'pr_id': pr_id,
        'comment_count': comment_count,
        'time_to_merge_minutes': time_to_merge,
        'review_cycles': review_cycles
    }

def join_and_save_metrics(
    labeled_prs: List[Dict[str, Any]],
    complexity_scores: Dict[int, float],
    output_path: Path
) -> List[Dict[str, Any]]:
    """
    Join labeled PRs with complexity scores and save to CSV.
    
    Args:
        labeled_prs: List of labeled PR dictionaries
        complexity_scores: Dictionary mapping pr_id to complexity_score
        output_path: Path for output CSV file
        
    Returns:
        List of joined metric dictionaries
    """
    metrics_list = []
    unmatched_prs = 0
    
    for pr in labeled_prs:
        pr_id = pr['pr_id']
        metrics = extract_pr_metrics(pr)
        
        # Join with complexity score
        if pr_id in complexity_scores:
            metrics['complexity_score'] = complexity_scores[pr_id]
        else:
            logger.warning(f"No complexity score found for PR {pr_id}, using None")
            metrics['complexity_score'] = None
            unmatched_prs += 1
        
        # Preserve source_type and other relevant fields
        metrics['source_type'] = pr.get('source_type', 'unknown')
        metrics['confidence_score'] = pr.get('confidence_score', 0.0)
        metrics['detector_score'] = pr.get('detector_score', 0.0)
        metrics['flagged'] = pr.get('flagged', False)
        
        metrics_list.append(metrics)
    
    if unmatched_prs > 0:
        logger.warning(f"Could not match {unmatched_prs} PRs with complexity scores")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to CSV
    fieldnames = [
        'pr_id', 'source_type', 'confidence_score', 'detector_score', 'flagged',
        'comment_count', 'time_to_merge_minutes', 'review_cycles', 'complexity_score'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for metrics in metrics_list:
            writer.writerow(metrics)
    
    logger.info(f"Saved {len(metrics_list)} PR metrics to {output_path}")
    return metrics_list

def run_extraction(
    labeled_prs_path: Path,
    complexity_scores_path: Path,
    output_path: Path
) -> List[Dict[str, Any]]:
    """
    Run the full extraction pipeline.
    
    Args:
        labeled_prs_path: Path to prs_labeled.csv
        complexity_scores_path: Path to complexity_scores.csv
        output_path: Path for output metrics CSV
        
    Returns:
        List of extracted and joined metrics
    """
    # Load data
    logger.info("Loading labeled PRs...")
    labeled_prs = load_prs_labeled(labeled_prs_path)
    
    logger.info("Loading complexity scores...")
    complexity_scores = load_complexity_scores(complexity_scores_path)
    
    # Join and save
    logger.info("Joining and saving metrics...")
    metrics = join_and_save_metrics(labeled_prs, complexity_scores, output_path)
    
    return metrics

def main():
    """Main entry point for the script."""
    setup_logging_and_config()
    
    # Define paths
    base_path = Path("data/processed")
    labeled_prs_path = base_path / "prs_labeled.csv"
    complexity_scores_path = base_path / "complexity_scores.csv"
    output_path = base_path / "prs_metrics.csv"
    
    try:
        metrics = run_extraction(labeled_prs_path, complexity_scores_path, output_path)
        logger.info(f"Successfully extracted metrics for {len(metrics)} PRs")
        print(f"Metrics saved to {output_path}")
    except FileNotFoundError as e:
        logger.error(f"Input file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during extraction: {e}")
        raise

if __name__ == "__main__":
    main()