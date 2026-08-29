"""
Task T024e: Metadata Aggregation & Subset Selection

Loads the metadata stats summary from T024, sorts datasets alphabetically,
selects the initial subset (using all available if limited), and flags
any shortfall in a report.

Output:
  - data/processed/metadata_stats_summary.csv (updated with subset flag if needed)
  - data/artifacts/metadata_subset_selection_report.json (report on selection)
"""
import os
import sys
import json
import csv
import argparse
from pathlib import Path
from datetime import datetime

# Ensure we can import from the project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import ensure_directories
from utils.logging import get_logger, log_info, log_error, log_warning

logger = get_logger(__name__)

def load_csv_data(input_path: Path) -> list[dict]:
    """Load the metadata stats summary CSV."""
    if not input_path.exists():
        log_error(f"Input file not found: {input_path}")
        return []
    
    data = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    log_info(f"Loaded {len(data)} rows from {input_path}")
    return data

def aggregate_metadata(data: list[dict], subset_size: int = None) -> tuple[list[dict], dict]:
    """
    Sort datasets alphabetically by dataset_id and select the initial subset.
    
    Args:
        data: List of dictionaries containing metadata stats.
        subset_size: Maximum number of datasets to include. If None, include all.
    
    Returns:
        tuple: (subsetted_data, report_dict)
    """
    if not data:
        log_warning("No data to process.")
        return [], {"selected_count": 0, "total_available": 0, "flagged": False}

    # Sort alphabetically by dataset_id
    sorted_data = sorted(data, key=lambda x: x.get('dataset_id', ''))
    
    total_available = len(sorted_data)
    selected_count = total_available
    flagged = False
    
    # If a subset size is specified and we have more than that, select the subset
    if subset_size is not None and total_available > subset_size:
        selected_count = subset_size
        flagged = True
        log_warning(f"Total available datasets ({total_available}) exceeds subset size ({subset_size}). Flagging shortfall.")
    
    subsetted_data = sorted_data[:selected_count]
    
    # Add a flag column if flagged
    if flagged:
        for row in subsetted_data:
            row['subset_selected'] = 'True'
        log_info(f"Added 'subset_selected' flag to {selected_count} rows.")
    else:
        # Explicitly mark all as selected if not flagged
        for row in subsetted_data:
            row['subset_selected'] = 'True'

    report = {
        "timestamp": datetime.now().isoformat(),
        "total_available": total_available,
        "selected_count": selected_count,
        "flagged_shortfall": flagged,
        "subset_size_limit": subset_size,
        "selected_dataset_ids": [row.get('dataset_id') for row in subsetted_data]
    }

    return subsetted_data, report

def save_summary_csv(data: list[dict], output_path: Path):
    """Save the processed data back to CSV."""
    ensure_directories([output_path])
    
    if not data:
        log_warning("No data to write to CSV.")
        # Write empty file with headers if possible, or just return
        return

    fieldnames = data[0].keys()
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    log_info(f"Saved {len(data)} rows to {output_path}")

def save_report_json(report: dict, output_path: Path):
    """Save the selection report to JSON."""
    ensure_directories([output_path])
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    log_info(f"Saved report to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Aggregate metadata stats and select subset (T024e)")
    parser.add_argument("--input", type=str, default="data/processed/metadata_stats_summary.csv",
                        help="Path to input summary CSV from T024")
    parser.add_argument("--output", type=str, default="data/processed/metadata_stats_summary.csv",
                        help="Path to output summary CSV")
    parser.add_argument("--report", type=str, default="data/artifacts/metadata_subset_selection_report.json",
                        help="Path to output report JSON")
    parser.add_argument("--subset-size", type=int, default=None,
                        help="Maximum number of datasets to select. If None, use all.")
    
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    report_path = Path(args.report)

    log_info(f"Starting T024e: Aggregating metadata stats from {input_path}")

    # Load data
    data = load_csv_data(input_path)
    if not data:
        log_error("Failed to load input data. Exiting.")
        sys.exit(1)

    # Aggregate and select subset
    subsetted_data, report = aggregate_metadata(data, subset_size=args.subset_size)

    # Save outputs
    save_summary_csv(subsetted_data, output_path)
    save_report_json(report, report_path)

    log_info("T024e completed successfully.")

if __name__ == "__main__":
    main()
