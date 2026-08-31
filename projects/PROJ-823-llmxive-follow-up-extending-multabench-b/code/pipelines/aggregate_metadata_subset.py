"""
Pipeline for T024e: Metadata Aggregation & Subset Selection.
Loads metadata stats, sorts alphabetically, selects initial subset, and flags shortfalls.
"""
import os
import sys
import json
import csv
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import get_logger, log_info, log_error, log_warning, log_critical

# Initialize logger
logger = get_logger("T024e_AggregateSubset")

def load_csv_data(csv_path: str) -> list:
    """Load metadata stats from CSV."""
    if not os.path.exists(csv_path):
        log_error(f"Input file not found: {csv_path}")
        return []
    
    data = []
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    log_info(f"Loaded {len(data)} datasets from {csv_path}")
    return data

def save_csv_data(data: list, csv_path: str):
    """Save metadata stats to CSV."""
    if not data:
        log_warning("No data to save.")
        return
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    
    fieldnames = data[0].keys()
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    log_info(f"Saved {len(data)} rows to {csv_path}")

def save_report_json(report: dict, json_path: str):
    """Save subset selection report to JSON."""
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    log_info(f"Saved report to {json_path}")

def aggregate_and_select_subset(data: list, subset_size: int = None) -> tuple:
    """
    Sort datasets alphabetically by dataset_id and select the initial subset.
    If subset_size is None or larger than available, use all and flag shortfall.
    
    Returns:
        tuple: (selected_data, report_dict)
    """
    if not data:
        log_warning("No data provided for subset selection.")
        return [], {"selected_count": 0, "total_available": 0, "shortfall_flagged": False}

    # Sort alphabetically by dataset_id
    sorted_data = sorted(data, key=lambda x: x.get('dataset_id', ''))
    total_available = len(sorted_data)

    # Determine selection size
    if subset_size is None or subset_size >= total_available:
        selected_data = sorted_data
        shortfall_flagged = False
        reason = "All available datasets selected (subset_size >= total or None)."
    else:
        selected_data = sorted_data[:subset_size]
        shortfall_flagged = True
        reason = f"Subset size limited to {subset_size} (requested {subset_size}, available {total_available})."

    # Add subset flag to selected data if needed
    for row in selected_data:
        if shortfall_flagged:
            row['subset_selected'] = 'true'
        else:
            row['subset_selected'] = 'all'

    report = {
        "selected_count": len(selected_data),
        "total_available": total_available,
        "shortfall_flagged": shortfall_flagged,
        "reason": reason,
        "selected_dataset_ids": [r['dataset_id'] for r in selected_data]
    }

    log_info(f"Subset selection complete: {len(selected_data)} of {total_available} datasets.")
    return selected_data, report

def main():
    parser = argparse.ArgumentParser(description="T024e: Aggregate Metadata and Select Subset")
    parser.add_argument("--input", type=str, default="data/processed/metadata_stats_summary.csv",
                        help="Path to input metadata stats CSV")
    parser.add_argument("--output", type=str, default="data/processed/metadata_stats_summary.csv",
                        help="Path to output CSV (overwrites input by default)")
    parser.add_argument("--report", type=str, default="data/artifacts/metadata_subset_report.json",
                        help="Path to output JSON report")
    parser.add_argument("--subset-size", type=int, default=None,
                        help="Maximum number of datasets to select. If None or > available, select all.")
    
    args = parser.parse_args()

    try:
        # 1. Load data
        data = load_csv_data(args.input)
        if not data:
            log_critical("No data loaded. Exiting.")
            sys.exit(1)

        # 2. Aggregate and Select Subset
        selected_data, report = aggregate_and_select_subset(data, args.subset_size)

        # 3. Save updated CSV
        save_csv_data(selected_data, args.output)

        # 4. Save Report
        save_report_json(report, args.report)

        log_info("T024e execution completed successfully.")

    except Exception as e:
        log_critical(f"Execution failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()