"""
T023: Save processed metrics to data/processed/prs_metrics.csv.

This script reads the metrics extracted by T022 (extract_metrics.py)
and saves them to the canonical location: data/processed/prs_metrics.csv.

Output Schema:
    pr_id (int), comment_count (int), time_to_merge_minutes (float),
    review_cycles (int), complexity_score (float)
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger, setup_logging
from utils.config import get_path

logger = None


def setup_logging_and_config(script_name: str = "save_metrics"):
    """Initialize logging and return config summary."""
    global logger
    # Use the tolerant logging setup
    logger = setup_logging()
    if logger is None:
        # Fallback if setup_logging returns None (tolerant logger)
        logger = get_logger(script_name)
    
    logger.log("setup_logging", operation="init", script=script_name)
    return get_path("processed")


def load_metrics_from_json(input_path: str) -> List[Dict[str, Any]]:
    """
    Load metrics from the JSON intermediate file produced by extract_metrics.py.
    
    Expected JSON structure: List[Dict] with keys:
        pr_id, comment_count, time_to_merge_minutes, review_cycles, complexity_score
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Metrics JSON file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.log("load_metrics", operation="read", file=input_path, count=len(data))
    return data


def save_metrics_to_csv(metrics: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save metrics to CSV with the required schema.
    
    Schema: pr_id, comment_count, time_to_merge_minutes, review_cycles, complexity_score
    """
    if not metrics:
        logger.log("save_metrics", operation="warning", message="No metrics to save")
        return

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fieldnames = [
        'pr_id',
        'comment_count',
        'time_to_merge_minutes',
        'review_cycles',
        'complexity_score'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in metrics:
            # Ensure all required fields are present and cast to correct types
            clean_row = {
                'pr_id': int(row.get('pr_id', 0)),
                'comment_count': int(row.get('comment_count', 0)),
                'time_to_merge_minutes': float(row.get('time_to_merge_minutes', 0.0)),
                'review_cycles': int(row.get('review_cycles', 0)),
                'complexity_score': float(row.get('complexity_score', 0.0))
            }
            writer.writerow(clean_row)
    
    logger.log("save_metrics", operation="write", file=output_path, count=len(metrics))


def run_save_metrics(input_path: str, output_path: str) -> None:
    """Main pipeline: load JSON metrics and save as CSV."""
    logger.log("run_save_metrics", operation="start", input=input_path, output=output_path)
    
    metrics = load_metrics_from_json(input_path)
    save_metrics_to_csv(metrics, output_path)
    
    logger.log("run_save_metrics", operation="complete", output=output_path)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Save processed metrics to CSV (T023)")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to input metrics JSON file (from extract_metrics.py)"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=False,
        default=None,
        help="Path to output CSV file (default: data/processed/prs_metrics.csv)"
    )
    
    args = parser.parse_args()
    
    # Initialize logging
    _ = setup_logging_and_config("save_metrics")
    
    # Determine output path
    if args.output is None:
        processed_dir = get_path("processed")
        output_path = os.path.join(processed_dir, "prs_metrics.csv")
    else:
        output_path = args.output
    
    try:
        run_save_metrics(args.input, output_path)
        print(f"Metrics saved to {output_path}")
        sys.exit(0)
    except Exception as e:
        logger.log("run_save_metrics", operation="error", error=str(e))
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()