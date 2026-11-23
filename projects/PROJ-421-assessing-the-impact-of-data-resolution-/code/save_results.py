import os
import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from utils import get_logger

logger = get_logger(__name__)

def load_analysis_results(results_dir: str) -> List[Dict[str, Any]]:
    """
    Load existing results from CSV if it exists, otherwise return empty list.
    """
    csv_path = Path(results_dir) / "results.csv"
    if not csv_path.exists():
        return []
    
    results = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric strings to floats/ints
            numeric_fields = ['resolution', 'moran_i', 'p_value', 'power', 'class_id']
            for field in numeric_fields:
                if field in row and row[field] is not None:
                    try:
                        if field == 'resolution':
                            row[field] = int(row[field])
                        elif field == 'class_id':
                            row[field] = int(row[field])
                        else:
                            row[field] = float(row[field])
                    except (ValueError, TypeError):
                        pass
            results.append(row)
    
    return results

def save_results_to_csv(
    results: List[Dict[str, Any]],
    output_path: str,
    append: bool = False
):
    """
    Save results to CSV. If append is True, adds to existing file.
    
    Args:
        results: List of result dictionaries.
        output_path: Path to the output CSV file.
        append: Whether to append to existing file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['resolution', 'moran_i', 'p_value', 'power', 'class_id']
    
    mode = 'a' if append else 'w'
    write_header = not append or not output_path.exists()
    
    with open(output_path, mode, newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        for row in results:
            writer.writerow(row)
    
    logger.info(f"Results saved to {output_path}")

def main():
    logger.info("Save results module ready.")

if __name__ == "__main__":
    main()
