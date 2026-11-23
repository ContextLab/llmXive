import csv
import os
from pathlib import Path
from typing import List, Dict, Any
from utils.logging import get_logger

logger = get_logger()

def save_metrics(metrics_list: List[Dict[str, Any]], output_path: str) -> None:
    """
    Append metrics to a CSV file at output_path.
    Creates the file and writes headers if it does not exist.
    
    Args:
        metrics_list: List of dictionaries containing metric keys and values.
        output_path: Path to the output CSV file (e.g., 'data/results/metrics.csv').
    """
    if not metrics_list:
        logger.warning("No metrics provided to save.")
        return

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Determine fieldnames from the first item if file doesn't exist
    if not output_file.exists():
        fieldnames = list(metrics_list[0].keys())
        write_mode = 'w'
    else:
        # Read existing headers to ensure consistency, though we assume schema matches
        with open(output_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            if not fieldnames:
                fieldnames = list(metrics_list[0].keys())
        write_mode = 'a'

    with open(output_file, write_mode, newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if write_mode == 'w':
            writer.writeheader()
        
        for row in metrics_list:
            # Ensure all keys in the row exist in fieldnames, otherwise add them if new
            # For this specific task, we expect a fixed schema.
            writer.writerow(row)
    
    logger.info(f"Saved {len(metrics_list)} metric records to {output_path}")
