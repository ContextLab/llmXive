"""
T024e: Metadata Aggregation & Subset Selection

Merges outputs from T024a-d (cardinality, missingness, sparsity, variance)
into a single summary CSV. Sorts alphabetically by dataset_id and selects
the initial subset (up to 20). If fewer than 20 are available, uses all
and flags the shortfall.

Output: data/processed/metadata_stats_summary.csv
"""
import os
import sys
import csv
import json
import argparse
from pathlib import Path
from datetime import datetime

# Ensure project root is in path for imports if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import ensure_directories
from utils.logging import get_logger, log_info, log_error, log_warning

logger = get_logger(__name__)

# Input file paths relative to project root
INPUT_FILES = {
    "cardinality": "data/processed/metadata_stats_cardinality.csv",
    "missingness": "data/processed/metadata_stats_missingness.csv",
    "sparsity": "data/processed/metadata_stats_sparsity.csv",
    "variance": "data/processed/metadata_stats_variance.csv"
}

OUTPUT_FILE = "data/processed/metadata_stats_summary.csv"
REPORT_FILE = "data/artifacts/metadata_aggregation_report.json"

def load_csv_data(filepath: str) -> dict:
    """Load a CSV file into a dictionary keyed by dataset_id."""
    data = {}
    path = PROJECT_ROOT / filepath
    if not path.exists():
        log_error(f"Input file not found: {filepath}")
        return None

    try:
        with open(path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Assume first column is dataset_id, second is the metric
                # Adjust based on actual column names if necessary
                keys = list(row.keys())
                if len(keys) < 2:
                    log_warning(f"Row in {filepath} has fewer than 2 columns: {row}")
                    continue
                dataset_id = row[keys[0]].strip()
                metric_value = row[keys[1]]
                try:
                    data[dataset_id] = float(metric_value)
                except ValueError:
                    log_warning(f"Could not parse metric value for {dataset_id} in {filepath}: {metric_value}")
                    data[dataset_id] = None  # Mark as missing
        return data
    except Exception as e:
        log_error(f"Error reading {filepath}: {e}")
        return None

def aggregate_metadata():
    """Main logic to aggregate metadata stats."""
    log_info("Starting metadata aggregation (T024e)...")
    
    # Ensure output directories exist
    ensure_directories()

    # Load all input files
    loaded_data = {}
    all_dataset_ids = set()
    
    missing_inputs = []
    for metric_name, filepath in INPUT_FILES.items():
        data = load_csv_data(filepath)
        if data is None:
            missing_inputs.append(filepath)
            loaded_data[metric_name] = {}
        else:
            loaded_data[metric_name] = data
            all_dataset_ids.update(data.keys())

    if not all_dataset_ids:
        log_error("No dataset IDs found in any input files.")
        return False

    if missing_inputs:
        log_warning(f"Missing input files: {missing_inputs}. Attempting to proceed with available data.")

    # Build the combined dataset
    combined_rows = []
    for dataset_id in all_dataset_ids:
        row = {"dataset_id": dataset_id}
        for metric_name in INPUT_FILES.keys():
            val = loaded_data[metric_name].get(dataset_id)
            row[metric_name] = val if val is not None else ""
        combined_rows.append(row)

    # Sort alphabetically by dataset_id
    combined_rows.sort(key=lambda x: x["dataset_id"])

    # Select subset (max 20)
    subset_size = 20
    selected_rows = combined_rows[:subset_size]
    total_available = len(combined_rows)
    flagged_shortfall = total_available < subset_size

    # Write output CSV
    output_path = PROJECT_ROOT / OUTPUT_FILE
    fieldnames = ["dataset_id"] + list(INPUT_FILES.keys())
    
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(selected_rows)
        log_info(f"Successfully wrote summary to {OUTPUT_FILE}")
    except Exception as e:
        log_error(f"Failed to write output CSV: {e}")
        return False

    # Generate report
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_datasets_available": total_available,
        "subset_size_selected": len(selected_rows),
        "max_subset_limit": subset_size,
        "flagged_shortfall": flagged_shortfall,
        "shortfall_reason": f"Only {total_available} datasets available, requested up to {subset_size}" if flagged_shortfall else None,
        "input_files_status": {k: "found" if k not in missing_inputs else "missing" for k in INPUT_FILES.keys()},
        "selected_dataset_ids": [r["dataset_id"] for r in selected_rows]
    }

    report_path = PROJECT_ROOT / REPORT_FILE
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        log_info(f"Successfully wrote aggregation report to {REPORT_FILE}")
    except Exception as e:
        log_error(f"Failed to write report JSON: {e}")
        return False

    if flagged_shortfall:
        log_warning(f"Shortfall flagged: Only {total_available} datasets available for analysis.")
    
    return True

def main():
    success = aggregate_metadata()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()