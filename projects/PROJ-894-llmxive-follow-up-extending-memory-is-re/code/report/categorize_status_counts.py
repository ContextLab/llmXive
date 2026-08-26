"""
Categorize status counts from all raw result CSVs.

Reads all raw result CSVs (T013, T013b, T019a, T019b, T019c, T019d)
and categorizes the counts of tasks that resulted in "TIMEOUT", "DEGENERATE",
and "UNRESOLVED" statuses.

Output: data/processed/status_counts.json
Keys broken down by strategy (Baseline, Lazy, Greedy) and by dataset (Clean, Noisy).
"""

import os
import json
import csv
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the CSV files and their metadata
# Format: (file_path, strategy_name, dataset_type)
# These correspond to the outputs of T013, T013b, T019a, T019b, T019c, T019d
CSV_FILES: List[Tuple[str, str, str]] = [
    ("data/processed/baseline_results.csv", "Baseline", "Clean"),
    ("data/processed/noisy_baseline_results.csv", "Baseline", "Noisy"),
    ("data/processed/lazy_results.csv", "Lazy", "Clean"),
    ("data/processed/noisy_lazy_results.csv", "Lazy", "Noisy"),
    ("data/processed/greedy_results.csv", "Greedy", "Clean"),
    ("data/processed/noisy_greedy_results.csv", "Greedy", "Noisy"),
]

# Statuses to count (SC-005 evidence specifically requires TIMEOUT counts)
TARGET_STATUSES = ["TIMEOUT", "DEGENERATE", "UNRESOLVED"]

def load_csv_status_counts(file_path: str) -> Tuple[Dict[str, int], int]:
    """
    Load a CSV file and count occurrences of each target status.

    Args:
        file_path: Path to the CSV file.

    Returns:
        Tuple of (dictionary mapping status to count, total row count).
        Returns ({status: 0...}, 0) if file is missing or invalid.
    """
    counts = {status: 0 for status in TARGET_STATUSES}
    total_rows = 0

    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path}. Skipping.")
        return counts, 0

    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # Check if 'status' column exists
            if reader.fieldnames is None or 'status' not in reader.fieldnames:
                logger.error(f"CSV file {file_path} does not have a 'status' column.")
                return counts, 0

            for row in reader:
                total_rows += 1
                status = row.get('status', '').strip().upper()
                if status in counts:
                    counts[status] += 1
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return counts, 0

    return counts, total_rows

def categorize_status_counts() -> Dict[str, Any]:
    """
    Read all raw result CSVs and categorize status counts.

    Returns:
        Dictionary with status counts broken down by strategy and dataset.
    """
    result = {
        "Baseline": {"Clean": {}, "Noisy": {}},
        "Lazy": {"Clean": {}, "Noisy": {}},
        "Greedy": {"Clean": {}, "Noisy": {}},
    }

    for file_path, strategy, dataset in CSV_FILES:
        logger.info(f"Processing {file_path} (Strategy: {strategy}, Dataset: {dataset})")
        counts, total_rows = load_csv_status_counts(file_path)

        # Store counts
        result[strategy][dataset] = {
            "status_counts": counts,
            "total_tasks": total_rows
        }

        # Log summary
        logger.info(f"  Total tasks: {total_rows}")
        for status, count in counts.items():
            if count > 0:
                logger.info(f"  {status}: {count}")

    return result

def save_results(result: Dict[str, Any], output_path: str) -> None:
    """
    Save the categorization results to a JSON file.

    Args:
        result: The categorization result dictionary.
        output_path: Path to the output JSON file.
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Results saved to {output_path}")

def main():
    """Main entry point."""
    logger.info("Starting status count categorization...")

    # Define output path
    output_path = "data/processed/status_counts.json"

    # Categorize counts
    result = categorize_status_counts()

    # Save results
    save_results(result, output_path)

    logger.info("Status count categorization completed.")

if __name__ == "__main__":
    main()