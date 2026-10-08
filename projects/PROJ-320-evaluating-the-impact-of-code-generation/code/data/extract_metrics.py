"""
T022 Implementation: Extract PR metrics and join with complexity scores.

Calculates comment_count, time_to_merge_minutes, and review_cycles for every PR
from data/processed/prs_labeled.csv and joins with data/processed/complexity_scores.csv
on pr_id.

Output: data/processed/prs_metrics.csv
Schema: pr_id (int), comment_count (int), time_to_merge_minutes (float),
        review_cycles (int), complexity_score (float)
"""
import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging import setup_logging, get_logger
from utils.config import get_path


def setup_logging_and_config(script_name: str = "extract_metrics") -> tuple:
    """Initialize logging and load configuration."""
    # Tolerant logging setup handling various call signatures seen in execution logs
    try:
        logger = setup_logging(script_name=script_name)
    except TypeError:
        try:
            logger = setup_logging(log_file=f"data/logs/{script_name}.log")
        except (TypeError, FileNotFoundError):
            # Fallback to default setup if arguments don't match
            logger = setup_logging()
    
    config = get_path()
    return logger, config


def load_prs_labeled(logger: Any, input_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load labeled PRs from data/processed/prs_labeled.csv.
    
    Args:
        logger: Logger instance
        input_path: Optional override for input path
        
    Returns:
        List of dictionaries containing PR data
    """
    path = input_path or get_path("processed", "prs_labeled.csv")
    logger.info(f"Loading labeled PRs from {path}")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Required input file not found: {path}. "
                              "Ensure T017 (save_labeled_dataset) has completed successfully.")
    
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    logger.info(f"Loaded {len(data)} labeled PRs")
    return data


def load_complexity_scores(logger: Any, input_path: Optional[str] = None) -> Dict[int, float]:
    """
    Load complexity scores from data/processed/complexity_scores.csv.
    
    Args:
        logger: Logger instance
        input_path: Optional override for input path
        
    Returns:
        Dictionary mapping pr_id to complexity_score
    """
    path = input_path or get_path("processed", "complexity_scores.csv")
    logger.info(f"Loading complexity scores from {path}")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Required input file not found: {path}. "
                              "Ensure T033b (save_complexity_scores) has completed successfully.")
    
    complexity_map = {}
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                pr_id = int(row['pr_id'])
                complexity_score = float(row['complexity_score'])
                complexity_map[pr_id] = complexity_score
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping malformed complexity row: {row} - {e}")
    
    logger.info(f"Loaded {len(complexity_map)} complexity scores")
    return complexity_map


def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
    """
    Parse various timestamp formats to datetime object.
    
    Args:
        timestamp_str: Timestamp string from GitHub API
        
    Returns:
        datetime object or None if parsing fails
    """
    if not timestamp_str:
        return None
    
    formats = [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue
    
    logger.warning(f"Could not parse timestamp: {timestamp_str}")
    return None


def calculate_time_to_merge_minutes(pr_data: Dict[str, Any]) -> float:
    """
    Calculate time to merge in minutes from created_at to merged_at.
    
    Args:
        pr_data: Dictionary containing PR data with timestamps
        
    Returns:
        Time to merge in minutes, or -1.0 if calculation fails
    """
    created_at = parse_timestamp(pr_data.get('created_at', ''))
    merged_at = parse_timestamp(pr_data.get('merged_at', ''))
    
    if created_at and merged_at and merged_at > created_at:
        delta = merged_at - created_at
        return delta.total_seconds() / 60.0
    
    return -1.0


def calculate_review_cycles(pr_data: Dict[str, Any]) -> int:
    """
    Calculate review cycles based on review events.
    
    A review cycle is counted when there are multiple review states
    (e.g., REQUEST_CHANGES -> COMMENT -> APPROVE).
    
    Args:
        pr_data: Dictionary containing PR data with review_events
        
    Returns:
        Number of review cycles
    """
    review_events = pr_data.get('review_events', [])
    if not review_events:
        return 0
    
    # Count state changes in reviews
    state_changes = 0
    prev_state = None
    
    for event in review_events:
        state = event.get('state', '').upper()
        if state and state != prev_state:
            if prev_state is not None:
                state_changes += 1
            prev_state = state
    
    return max(1, state_changes) if state_changes > 0 else 0


def extract_comment_count(pr_data: Dict[str, Any]) -> int:
    """
    Extract total comment count from PR data.
    
    Args:
        pr_data: Dictionary containing PR data
        
    Returns:
        Total comment count
    """
    # Sum of comments and review comments
    comments = int(pr_data.get('comments', 0))
    review_comments = int(pr_data.get('review_comments', 0))
    return comments + review_comments


def extract_pr_metrics(prs: List[Dict[str, Any]], logger: Any) -> List[Dict[str, Any]]:
    """
    Extract metrics for all PRs.
    
    Args:
        prs: List of PR dictionaries
        logger: Logger instance
        
    Returns:
        List of dictionaries with extracted metrics
    """
    metrics = []
    
    for pr in prs:
        try:
            pr_id = int(pr.get('pr_id', pr.get('id', 0)))
            comment_count = extract_comment_count(pr)
            time_to_merge = calculate_time_to_merge_minutes(pr)
            review_cycles = calculate_review_cycles(pr)
            
            metrics.append({
                'pr_id': pr_id,
                'comment_count': comment_count,
                'time_to_merge_minutes': time_to_merge,
                'review_cycles': review_cycles
            })
            
        except (ValueError, KeyError) as e:
            logger.warning(f"Skipping PR due to extraction error: {pr.get('pr_id', 'unknown')} - {e}")
            continue
    
    logger.info(f"Extracted metrics for {len(metrics)} PRs")
    return metrics


def join_and_save_metrics(
    metrics: List[Dict[str, Any]], 
    complexity_map: Dict[int, float], 
    output_path: str,
    logger: Any
) -> bool:
    """
    Join metrics with complexity scores and save to CSV.
    
    Args:
        metrics: List of metric dictionaries
        complexity_map: Dictionary mapping pr_id to complexity_score
        output_path: Path for output CSV
        logger: Logger instance
        
    Returns:
        True if successful, False otherwise
    """
    joined_data = []
    skipped_count = 0
    
    for metric in metrics:
        pr_id = metric['pr_id']
        complexity_score = complexity_map.get(pr_id, -1.0)
        
        if pr_id not in complexity_map:
            skipped_count += 1
            logger.warning(f"Complexity score missing for PR {pr_id}, using -1.0")
        
        joined_data.append({
            'pr_id': pr_id,
            'comment_count': metric['comment_count'],
            'time_to_merge_minutes': metric['time_to_merge_minutes'],
            'review_cycles': metric['review_cycles'],
            'complexity_score': complexity_score
        })
    
    if skipped_count > 0:
        logger.warning(f"Skipped {skipped_count} PRs due to missing complexity scores")
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # Write to CSV
    fieldnames = ['pr_id', 'comment_count', 'time_to_merge_minutes', 'review_cycles', 'complexity_score']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(joined_data)
    
    logger.info(f"Saved {len(joined_data)} joined metrics to {output_path}")
    return True


def run_extraction(
    labeled_path: Optional[str] = None,
    complexity_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> bool:
    """
    Main extraction pipeline.
    
    Args:
        labeled_path: Path to labeled PRs CSV
        complexity_path: Path to complexity scores CSV
        output_path: Path for output metrics CSV
        
    Returns:
        True if successful, False otherwise
    """
    logger, config = setup_logging_and_config()
    logger.info("Starting PR metrics extraction pipeline (T022)")
    
    try:
        # Load inputs
        prs_labeled = load_prs_labeled(logger, labeled_path)
        complexity_scores = load_complexity_scores(logger, complexity_path)
        
        # Extract metrics
        metrics = extract_pr_metrics(prs_labeled, logger)
        
        # Set output path
        out_path = output_path or get_path("processed", "prs_metrics.csv")
        
        # Join and save
        success = join_and_save_metrics(metrics, complexity_scores, out_path, logger)
        
        if success:
            logger.info("Pipeline completed successfully")
            return True
        else:
            logger.error("Pipeline failed during save")
            return False
            
    except FileNotFoundError as e:
        logger.error(f"Input file error: {e}")
        return False
    except Exception as e:
        logger.error(f"Pipeline failed with unexpected error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Extract PR metrics and join with complexity scores (T022)"
    )
    parser.add_argument(
        "--labeled-input",
        type=str,
        default=None,
        help="Path to labeled PRs CSV (default: data/processed/prs_labeled.csv)"
    )
    parser.add_argument(
        "--complexity-input",
        type=str,
        default=None,
        help="Path to complexity scores CSV (default: data/processed/complexity_scores.csv)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path for output metrics CSV (default: data/processed/prs_metrics.csv)"
    )
    
    args = parser.parse_args()
    
    success = run_extraction(
        labeled_path=args.labeled_input,
        complexity_path=args.complexity_input,
        output_path=args.output
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()