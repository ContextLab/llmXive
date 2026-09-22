"""
Extract review metrics from labeled PRs and join with complexity scores.

This script calculates comment_count, time_to_merge_minutes, and review_cycles
for every PR from data/processed/prs_labeled.csv and joins with
data/processed/complexity_scores.csv (produced by T033) to include the
actual complexity_score.

Output: data/processed/prs_metrics.csv
Schema: pr_id (int), comment_count (int), time_to_merge_minutes (float),
        review_cycles (int), complexity_score (float)
"""

import os
import csv
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import from project utils
from utils.logging import get_logger, setup_logging
from utils.config import get_path

# Setup logging
logger = get_logger(__name__)
setup_logging()

def setup_logging_and_config():
    """Initialize logging and configuration."""
    return logger

def load_prs_labeled(logger: Any) -> List[Dict[str, Any]]:
    """
    Load the labeled PRs dataset from data/processed/prs_labeled.csv.

    Returns a list of dictionaries with PR data including:
    - pr_id: int
    - created_at: str (ISO format)
    - merged_at: str (ISO format) or None
    - comment_count: int
    - review_cycles: int (derived from review events if available)
    - source_type: str ('llm' or 'human')
    """
    input_path = get_path("processed_prs_labeled")
    logger.info(f"Loading labeled PRs from {input_path}")

    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Required input file not found: {input_path}. "
            "Ensure T017 (save_labeled_dataset) has completed successfully."
        )

    prs = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            prs.append({
                'pr_id': int(row['pr_id']),
                'created_at': row.get('created_at'),
                'merged_at': row.get('merged_at'),
                'comment_count': int(row.get('comment_count', 0)),
                'review_cycles': int(row.get('review_cycles', 0)),
                'source_type': row.get('source_type', 'unknown'),
                'confidence_score': float(row.get('confidence_score', 0.0)),
                'flagged': row.get('flagged', 'False') == 'True',
                'detector_score': float(row.get('detector_score', 0.0))
            })

    logger.info(f"Loaded {len(prs)} PRs from labeled dataset")
    return prs

def load_complexity_scores(logger: Any) -> Dict[int, float]:
    """
    Load complexity scores from data/processed/complexity_scores.csv.

    Returns a dictionary mapping pr_id -> complexity_score.
    """
    input_path = get_path("processed_complexity_scores")
    logger.info(f"Loading complexity scores from {input_path}")

    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Required input file not found: {input_path}. "
            "Ensure T033 (save_complexity_scores) has completed successfully."
        )

    complexity_map = {}
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pr_id = int(row['pr_id'])
            complexity_score = float(row['complexity_score'])
            complexity_map[pr_id] = complexity_score

    logger.info(f"Loaded complexity scores for {len(complexity_map)} PRs")
    return complexity_map

def parse_timestamp(timestamp_str: Optional[str]) -> Optional[datetime]:
    """
    Parse an ISO format timestamp string to datetime object.

    Handles common GitHub API timestamp formats.
    """
    if not timestamp_str:
        return None

    try:
        # Try standard ISO format
        return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except ValueError:
        try:
            # Try alternative formats
            return datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            logger.warning(f"Could not parse timestamp: {timestamp_str}")
            return None

def calculate_time_to_merge_minutes(created_at: Optional[str], merged_at: Optional[str]) -> Optional[float]:
    """
    Calculate time-to-merge in minutes between PR creation and merge.

    Returns None if either timestamp is missing or merge didn't occur.
    """
    if not created_at or not merged_at:
        return None

    created_dt = parse_timestamp(created_at)
    merged_dt = parse_timestamp(merged_at)

    if not created_dt or not merged_dt:
        return None

    if merged_dt < created_dt:
        logger.warning(f"Invalid timestamps: merged_at < created_at for PR")
        return None

    delta = merged_dt - created_dt
    return delta.total_seconds() / 60.0

def calculate_review_cycles(review_events: Optional[List[Dict[str, Any]]]) -> int:
    """
    Calculate the number of review cycles from review events.

    A review cycle is counted when there's a review request or approval/rejection
    that indicates a round of feedback. For simplicity, we count unique
    review sessions or rounds.

    Args:
        review_events: List of review event dictionaries

    Returns:
        int: Number of review cycles (minimum 0)
    """
    if not review_events:
        return 0

    # Count distinct review cycles based on state changes
    # This is a simplified heuristic; real implementation would parse
    # the actual review event sequence
    cycles = 0
    last_state = None

    for event in review_events:
        state = event.get('state', '').lower()
        if state in ['approved', 'changes_requested', 'commented']:
            if state != last_state:
                cycles += 1
                last_state = state

    return cycles

def extract_comment_count(pr_data: Dict[str, Any]) -> int:
    """
    Extract the comment count from PR data.

    Args:
        pr_data: Dictionary containing PR information

    Returns:
        int: Number of comments on the PR
    """
    return int(pr_data.get('comment_count', 0))

def extract_pr_metrics(
    pr: Dict[str, Any],
    complexity_map: Dict[int, float],
    logger: Any
) -> Dict[str, Any]:
    """
    Extract all metrics for a single PR.

    Args:
        pr: Labeled PR data dictionary
        complexity_map: Dictionary mapping pr_id to complexity_score
        logger: Logger instance

    Returns:
        Dictionary with all extracted metrics
    """
    pr_id = pr['pr_id']

    # Calculate time to merge
    time_to_merge = calculate_time_to_merge_minutes(
        pr.get('created_at'),
        pr.get('merged_at')
    )

    # Get comment count (already in labeled data, but re-extract for clarity)
    comment_count = extract_comment_count(pr)

    # Get review cycles (already in labeled data, but re-extract for clarity)
    review_cycles = pr.get('review_cycles', 0)

    # Get complexity score from joined data
    complexity_score = complexity_map.get(pr_id)
    if complexity_score is None:
        logger.warning(f"PR {pr_id} not found in complexity scores. Using 0.0")
        complexity_score = 0.0

    return {
        'pr_id': pr_id,
        'comment_count': comment_count,
        'time_to_merge_minutes': time_to_merge if time_to_merge is not None else 0.0,
        'review_cycles': review_cycles,
        'complexity_score': complexity_score,
        'source_type': pr.get('source_type', 'unknown')
    }

def join_and_save_metrics(
    prs: List[Dict[str, Any]],
    complexity_map: Dict[int, float],
    output_path: str,
    logger: Any
) -> int:
    """
    Join PRs with complexity scores and save to CSV.

    Args:
        prs: List of labeled PR dictionaries
        complexity_map: Dictionary mapping pr_id to complexity_score
        output_path: Path for output CSV file
        logger: Logger instance

    Returns:
        int: Number of records written
    """
    logger.info(f"Joining {len(prs)} PRs with complexity scores")

    metrics = []
    for pr in prs:
        metric_row = extract_pr_metrics(pr, complexity_map, logger)
        metrics.append(metric_row)

    # Write to CSV
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fieldnames = ['pr_id', 'comment_count', 'time_to_merge_minutes',
                  'review_cycles', 'complexity_score', 'source_type']

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for metric in metrics:
            writer.writerow(metric)

    logger.info(f"Wrote {len(metrics)} metrics to {output_path}")
    return len(metrics)

def run_extraction(logger: Any) -> bool:
    """
    Main extraction pipeline: load data, join, and save metrics.

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Load input data
        prs = load_prs_labeled(logger)
        complexity_map = load_complexity_scores(logger)

        if not prs:
            logger.error("No PRs found in labeled dataset")
            return False

        if not complexity_map:
            logger.error("No complexity scores found")
            return False

        # Define output path
        output_path = get_path("processed_prs_metrics")

        # Join and save
        count = join_and_save_metrics(prs, complexity_map, output_path, logger)

        logger.info(f"Extraction complete: {count} records written to {output_path}")
        return True

    except FileNotFoundError as e:
        logger.error(f"Input file error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during extraction: {e}", exc_info=True)
        return False

def main():
    """Entry point for the script."""
    logger = setup_logging_and_config()
    logger.info("Starting PR metrics extraction pipeline (T022)")

    success = run_extraction(logger)

    if success:
        logger.info("Pipeline completed successfully")
        return 0
    else:
        logger.error("Pipeline failed")
        return 1

if __name__ == "__main__":
    exit(main())