"""
Pipeline script to aggregate metadata statistics from T024a-d into a single summary CSV.

This script merges the outputs of:
- code/analysis/metadata_stats.py::compute_cardinality -> data/processed/metadata_stats_cardinality.csv
- code/analysis/metadata_stats.py::compute_missingness -> data/processed/metadata_stats_missingness.csv
- code/analysis/metadata_stats.py::compute_sparsity -> data/processed/metadata_stats_sparsity.csv
- code/analysis/metadata_stats.py::compute_variance -> data/processed/metadata_stats_variance.csv

It sorts datasets alphabetically by dataset_id, selects the initial subset (up to 20),
and writes the result to data/processed/metadata_stats_summary.csv.
"""

import os
import sys
import csv
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import ensure_directories
from utils.logging import get_logger, log_info, log_warning, log_error

logger = get_logger(__name__)

# Constants
DATA_PROCESSED_DIR = Path("data/processed")
INPUT_FILES = {
    "cardinality": DATA_PROCESSED_DIR / "metadata_stats_cardinality.csv",
    "missingness": DATA_PROCESSED_DIR / "metadata_stats_missingness.csv",
    "sparsity": DATA_PROCESSED_DIR / "metadata_stats_sparsity.csv",
    "variance": DATA_PROCESSED_DIR / "metadata_stats_variance.csv",
}
OUTPUT_FILE = DATA_PROCESSED_DIR / "metadata_stats_summary.csv"
MAX_DATASETS = 20


def load_csv_data(file_path: Path) -> dict:
    """
    Load a CSV file and return a dictionary mapping dataset_id to its value.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        Dictionary: {dataset_id: value}
    """
    data = {}
    if not file_path.exists():
        log_error(f"Input file not found: {file_path}")
        return data
    
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Handle potential missing columns gracefully
                dataset_id = row.get('dataset_id', '').strip()
                if not dataset_id:
                    continue
                
                # Try to find the value column (could be 'value', 'cardinality', etc.)
                value = None
                for col in ['value', row.keys()]:
                    if isinstance(col, str) and col in row and row[col]:
                        try:
                            value = float(row[col])
                            break
                        except (ValueError, TypeError):
                            continue
                
                if value is None:
                    # Try the second column if it exists
                    keys = list(row.keys())
                    if len(keys) > 1:
                        try:
                            value = float(row[keys[1]])
                        except (ValueError, TypeError):
                            log_warning(f"Could not parse value for {dataset_id} in {file_path}")
                            continue
                
                if value is not None:
                    data[dataset_id] = value
                    
    except Exception as e:
        log_error(f"Error reading {file_path}: {e}")
    
    return data


def aggregate_metadata() -> dict:
    """
    Aggregate metadata from all input files into a single dictionary.
    
    Returns:
        Dictionary: {dataset_id: {cardinality: x, missingness: y, sparsity: z, variance: w}}
    """
    # Load all input data
    cardinality_data = load_csv_data(INPUT_FILES["cardinality"])
    missingness_data = load_csv_data(INPUT_FILES["missingness"])
    sparsity_data = load_csv_data(INPUT_FILES["sparsity"])
    variance_data = load_csv_data(INPUT_FILES["variance"])
    
    # Find all unique dataset IDs
    all_dataset_ids = set()
    all_dataset_ids.update(cardinality_data.keys())
    all_dataset_ids.update(missingness_data.keys())
    all_dataset_ids.update(sparsity_data.keys())
    all_dataset_ids.update(variance_data.keys())
    
    if not all_dataset_ids:
        log_error("No datasets found in any input files.")
        return {}
    
    log_info(f"Found {len(all_dataset_ids)} unique datasets across input files.")
    
    # Aggregate data
    aggregated = {}
    for dataset_id in all_dataset_ids:
        aggregated[dataset_id] = {
            "cardinality": cardinality_data.get(dataset_id),
            "missingness": missingness_data.get(dataset_id),
            "sparsity": sparsity_data.get(dataset_id),
            "variance": variance_data.get(dataset_id),
        }
    
    return aggregated


def save_summary_csv(aggregated_data: dict, output_path: Path, max_datasets: int = MAX_DATASETS):
    """
    Save the aggregated metadata to a CSV file, sorted alphabetically by dataset_id.
    
    Args:
        aggregated_data: Dictionary of aggregated metadata
        output_path: Path to the output CSV file
        max_datasets: Maximum number of datasets to include (default: 20)
    """
    # Sort datasets alphabetically
    sorted_dataset_ids = sorted(aggregated_data.keys())
    
    # Select subset if necessary
    selected_dataset_ids = sorted_dataset_ids[:max_datasets]
    total_available = len(sorted_dataset_ids)
    
    if total_available < max_datasets:
        log_warning(f"Only {total_available} datasets available, which is less than the requested {max_datasets}. Using all available.")
    elif total_available > max_datasets:
        log_info(f"Selected top {max_datasets} datasets out of {total_available} available (sorted alphabetically).")
    
    # Ensure output directory exists
    ensure_directories()
    
    # Write CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['dataset_id', 'cardinality', 'missingness', 'sparsity', 'variance']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for dataset_id in selected_dataset_ids:
            row = {
                'dataset_id': dataset_id,
                'cardinality': aggregated_data[dataset_id]['cardinality'],
                'missingness': aggregated_data[dataset_id]['missingness'],
                'sparsity': aggregated_data[dataset_id]['sparsity'],
                'variance': aggregated_data[dataset_id]['variance'],
            }
            writer.writerow(row)
    
    log_info(f"Successfully wrote summary to {output_path}")
    
    # Generate a report about the subset selection
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_datasets_available": total_available,
        "datasets_selected": len(selected_dataset_ids),
        "max_datasets_allowed": max_datasets,
        "shortfall_flagged": total_available < max_datasets,
        "selected_dataset_ids": selected_dataset_ids,
        "output_file": str(output_path)
    }
    
    report_path = output_path.with_suffix('.json').with_suffix('.json').with_suffix('')
    report_path = output_path.parent / f"{output_path.stem}_selection_report.json"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    log_info(f"Selection report written to {report_path}")
    
    return report


def main():
    """Main entry point for the aggregation pipeline."""
    parser = argparse.ArgumentParser(
        description="Aggregate metadata statistics from T024a-d into a single summary CSV."
    )
    parser.add_argument(
        "--max-datasets",
        type=int,
        default=MAX_DATASETS,
        help=f"Maximum number of datasets to include in the summary (default: {MAX_DATASETS})"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(OUTPUT_FILE),
        help=f"Path to the output CSV file (default: {OUTPUT_FILE})"
    )
    
    args = parser.parse_args()
    
    log_info("Starting metadata aggregation pipeline...")
    
    # Aggregate data
    aggregated_data = aggregate_metadata()
    
    if not aggregated_data:
        log_error("Aggregation failed: no data found.")
        sys.exit(1)
    
    # Save summary
    output_path = Path(args.output)
    save_summary_csv(aggregated_data, output_path, args.max_datasets)
    
    log_info("Metadata aggregation pipeline completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
