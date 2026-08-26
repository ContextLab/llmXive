import os
import sys
import csv
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import ensure_directories
from utils.logging import get_logger, log_info, log_warning, log_error

logger = get_logger(__name__)

INPUT_FILES = [
    "data/processed/metadata_stats_cardinality.csv",
    "data/processed/metadata_stats_missingness.csv",
    "data/processed/metadata_stats_sparsity.csv",
    "data/processed/metadata_stats_variance.csv"
]

OUTPUT_FILE = "data/processed/metadata_stats_summary.csv"
MAX_DATASETS = 20
REPORT_FILE = "data/artifacts/metadata_subset_selection_report.json"

def load_csv_data(file_path: str) -> dict:
    """
    Load a CSV file and return a dictionary mapping dataset_id to the value.
    Expects columns: dataset_id, <metric_name>
    """
    data = {}
    if not os.path.exists(file_path):
        log_error(f"Input file not found: {file_path}")
        return None

    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            dataset_id = row.get('dataset_id')
            if not dataset_id:
                log_warning(f"Skipping row with missing dataset_id in {file_path}")
                continue
            # Assume the second column is the value
            val = row.get(list(row.keys())[1])
            try:
                data[dataset_id] = float(val)
            except (ValueError, TypeError):
                log_warning(f"Could not convert value to float for {dataset_id} in {file_path}")
                data[dataset_id] = None
    return data

def aggregate_metadata():
    """
    Merges outputs of T024a-d into a single CSV, sorts alphabetically,
    selects the initial subset (up to 20), and flags shortfalls.
    """
    ensure_directories()

    log_info("Starting metadata aggregation...")

    # Load all component files
    datasets = {}
    metrics = {
        'cardinality': load_csv_data(INPUT_FILES[0]),
        'missingness': load_csv_data(INPUT_FILES[1]),
        'sparsity': load_csv_data(INPUT_FILES[2]),
        'variance': load_csv_data(INPUT_FILES[3])
    }

    if any(m is None for m in metrics.values()):
        log_error("One or more input files are missing or empty. Cannot proceed.")
        return False

    # Collect all unique dataset IDs present in ALL files
    # We only include datasets that have data in all 4 metrics
    all_ids = set(metrics['cardinality'].keys())
    for metric_name, data in metrics.items():
        all_ids &= set(data.keys())

    if not all_ids:
        log_error("No common datasets found across all input files.")
        return False

    # Sort alphabetically
    sorted_ids = sorted(list(all_ids))

    # Select subset
    selected_ids = sorted_ids[:MAX_DATASETS]
    shortfall = len(sorted_ids) < MAX_DATASETS
    skipped_ids = sorted_ids[MAX_DATASETS:] if len(sorted_ids) > MAX_DATASETS else []

    log_info(f"Found {len(sorted_ids)} common datasets.")
    log_info(f"Selected {len(selected_ids)} datasets (max {MAX_DATASETS}).")
    if shortfall:
        log_warning(f"Shortfall: Only {len(sorted_ids)} datasets available (needed {MAX_DATASETS}).")
    if skipped_ids:
        log_info(f"Excluded {len(skipped_ids)} datasets due to limit.")

    # Build summary rows
    rows = []
    for ds_id in selected_ids:
        row = {
            'dataset_id': ds_id,
            'cardinality': metrics['cardinality'][ds_id],
            'missingness': metrics['missingness'][ds_id],
            'sparsity': metrics['sparsity'][ds_id],
            'variance': metrics['variance'][ds_id]
        }
        rows.append(row)

    # Write output CSV
    output_path = Path(OUTPUT_FILE)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['dataset_id', 'cardinality', 'missingness', 'sparsity', 'variance']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    log_info(f"Summary written to {output_path}")

    # Write report JSON
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_datasets_found': len(sorted_ids),
        'datasets_selected': len(selected_ids),
        'max_datasets_allowed': MAX_DATASETS,
        'shortfall_flagged': shortfall,
        'selected_dataset_ids': selected_ids,
        'excluded_dataset_ids': skipped_ids,
        'input_files': INPUT_FILES,
        'output_file': str(output_path)
    }

    report_path = Path(REPORT_FILE)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    log_info(f"Selection report written to {report_path}")
    return True

def main():
    success = aggregate_metadata()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
