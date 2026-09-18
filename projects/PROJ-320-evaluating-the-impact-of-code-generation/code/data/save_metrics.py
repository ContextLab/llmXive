"""
Save processed metrics to data/processed/prs_metrics.csv.

This script reads the joined metrics data (produced by extract_metrics.py)
and saves it to the final CSV format required for analysis.

Output: data/processed/prs_metrics.csv with columns:
- pr_id (int)
- source_type (str)
- comment_count (int)
- time_to_merge_minutes (float)
- review_cycles (int)
- complexity_score (float)
"""
import os
import csv
import json
from pathlib import Path
from typing import List, Dict, Any
from utils.logging import get_logger, setup_logging

logger = None

def setup_logging_and_config():
    """Initialize logging and load configuration."""
    global logger
    logger = setup_logging("save_metrics")
    logger.info("Starting metrics saving pipeline")

def load_metrics_from_json(json_path: Path) -> List[Dict[str, Any]]:
    """Load metrics data from the JSON file produced by extract_metrics.py."""
    if not json_path.exists():
        raise FileNotFoundError(f"Input file not found: {json_path}")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.info(f"Loaded {len(data)} records from {json_path}")
    return data

def save_metrics_to_csv(metrics: List[Dict[str, Any]], output_path: Path):
    """Save metrics to CSV with required columns."""
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        'pr_id',
        'source_type', 
        'comment_count',
        'time_to_merge_minutes',
        'review_cycles',
        'complexity_score'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in metrics:
            # Ensure all required fields are present
            row = {
                'pr_id': int(record['pr_id']),
                'source_type': str(record['source_type']),
                'comment_count': int(record['comment_count']),
                'time_to_merge_minutes': float(record['time_to_merge_minutes']),
                'review_cycles': int(record['review_cycles']),
                'complexity_score': float(record['complexity_score'])
            }
            writer.writerow(row)
    
    logger.info(f"Saved {len(metrics)} records to {output_path}")

def run_save_metrics():
    """Main execution function for saving metrics."""
    setup_logging_and_config()
    
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    input_json = project_root / "data" / "processed" / "pr_metrics_with_complexity.json"
    output_csv = project_root / "data" / "processed" / "prs_metrics.csv"
    
    logger.info(f"Input: {input_json}")
    logger.info(f"Output: {output_csv}")
    
    # Load metrics
    metrics = load_metrics_from_json(input_json)
    
    # Validate data
    if not metrics:
        logger.error("No metrics data to save")
        return
    
    required_fields = ['pr_id', 'source_type', 'comment_count', 'time_to_merge_minutes', 
                     'review_cycles', 'complexity_score']
    for field in required_fields:
        if field not in metrics[0]:
            raise ValueError(f"Missing required field: {field}")
    
    # Save to CSV
    save_metrics_to_csv(metrics, output_csv)
    
    logger.info("Metrics saving completed successfully")
    return output_csv

def main():
    """Entry point for script execution."""
    try:
        output_path = run_save_metrics()
        if output_path:
            print(f"Successfully saved metrics to: {output_path}")
            print(f"File exists: {output_path.exists()}")
            print(f"File size: {output_path.stat().st_size} bytes")
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()