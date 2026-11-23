"""
Logging utilities for saving results and exclusions.
"""
import csv
import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def ensure_output_dir(file_path: str):
    """Ensure the directory for a file path exists."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

def save_results_to_csv(data: List[Dict[str, Any]], output_path: str, fieldnames: Optional[List[str]] = None):
    """Save a list of dictionaries to a CSV file."""
    ensure_output_dir(output_path)
    if not data:
        logger.warning(f"No data to save to {output_path}")
        return

    if fieldnames is None:
        fieldnames = list(data[0].keys())

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def save_results_to_json(data: Any, output_path: str):
    """Save data to a JSON file."""
    ensure_output_dir(output_path)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

def serialize_entropy_results(results: List[Dict]) -> List[Dict]:
    """Prepare entropy results for serialization."""
    return results

def serialize_convergence_results(results: List[Dict]) -> List[Dict]:
    """Prepare convergence results for serialization."""
    return results

def log_exclusions(exclusions: List[Dict], output_path: str):
    """Log excluded items to a JSON file."""
    save_results_to_json(exclusions, output_path)
    logger.info(f"Logged {len(exclusions)} exclusions to {output_path}")

def main():
    # Test
    test_data = [{"a": 1, "b": 2}]
    save_results_to_csv(test_data, "data/test.csv")
    print("Test CSV saved.")

if __name__ == "__main__":
    main()
