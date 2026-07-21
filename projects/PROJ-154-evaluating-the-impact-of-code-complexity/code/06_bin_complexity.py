import os
import sys
import json
import logging
import csv
from pathlib import Path

# Import logging utilities from the project's existing API surface
from utils.logging_config import setup_deterministic_logging, set_seed, get_logger

# Setup deterministic logging as per Constitution VII
setup_deterministic_logging()
logger = get_logger(__name__)
set_seed(42)

def load_annotated_data(csv_path: str) -> list[dict]:
    """
    Load the annotated metrics CSV into a list of dictionaries.
    Expects columns: snippet_id, code, ground_truth, cc, halstead_volume, maintainability_index
    """
    data = []
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Annotated data file not found: {csv_path}")

    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Ensure numeric columns are floats
            try:
                row['cc'] = float(row['cc'])
                row['halstead_volume'] = float(row['halstead_volume'])
                row['maintainability_index'] = float(row['maintainability_index'])
                data.append(row)
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping row due to invalid numeric data: {e}")
                continue
    return data

def calculate_tertiles(values: list[float]) -> tuple[float, float]:
    """
    Calculate the boundaries for Low, Medium, and High tertiles.
    Returns (lower_boundary, upper_boundary).
    Low: value <= lower
    Medium: lower < value <= upper
    High: value > upper
    """
    if not values:
        return 0.0, 0.0
    
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    
    # Calculate indices for 33.33% and 66.66%
    idx1 = int(n / 3)
    idx2 = int(2 * n / 3)
    
    # Use simple index-based cutoffs for tertiles
    # If n=100, idx1=33, idx2=66. 
    # Values at these indices define the boundaries.
    lower_boundary = sorted_vals[idx1]
    upper_boundary = sorted_vals[idx2]
    
    return lower_boundary, upper_boundary

def assign_bin(value: float, lower: float, upper: float) -> str:
    """Assign a bin label based on tertile boundaries."""
    if value <= lower:
        return "Low"
    elif value <= upper:
        return "Medium"
    else:
        return "High"

def bin_complexity_metrics(data: list[dict], metric_name: str) -> dict:
    """
    Calculate tertiles for a specific metric and assign bins to each row.
    Returns the updated data list and the boundaries.
    """
    values = [row[metric_name] for row in data]
    lower, upper = calculate_tertiles(values)
    
    for row in data:
        row[f"{metric_name}_bin"] = assign_bin(row[metric_name], lower, upper)
    
    return data, lower, upper

def save_binned_data(data: list[dict], output_path: str):
    """Save the binned data to a new CSV file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if not data:
        logger.warning("No data to save.")
        return

    fieldnames = list(data[0].keys())
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"Binned data saved to {output_path}")

def update_metadata(metadata_path: str, boundaries: dict):
    """
    Update the metadata.json file with the calculated binning boundaries.
    This satisfies Constitution VII requirement to explicitly write boundaries.
    """
    path = Path(metadata_path)
    if not path.exists():
        # Initialize if missing
        metadata = {
            "total_raw_snippets": 0,
            "total_valid_snippets": 0,
            "total_excluded_snippets": 0,
            "last_annotation_run": None,
            "annotation_status": "pending",
            "binning_boundaries": {}
        }
    else:
        with open(path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    
    metadata["binning_boundaries"] = boundaries
    metadata["binning_status"] = "completed"
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Metadata updated with binning boundaries at {metadata_path}")

def main():
    """
    Main entry point for T017: Binning Strategy Implementation.
    
    1. Loads data from data/processed/annotated_metrics.csv
    2. Calculates tertiles for CC, Halstead, and Maintainability
    3. Assigns Low/Medium/High bins
    4. Saves binned data to data/processed/binned_metrics.csv
    5. Updates data/processed/metadata.json with the exact boundary values
    """
    project_root = Path(__file__).resolve().parent.parent
    input_csv = project_root / "data" / "processed" / "annotated_metrics.csv"
    output_csv = project_root / "data" / "processed" / "binned_metrics.csv"
    metadata_file = project_root / "data" / "processed" / "metadata.json"
    
    if not input_csv.exists():
        logger.error(f"Input file not found: {input_csv}")
        sys.exit(1)
    
    logger.info(f"Loading annotated data from {input_csv}")
    data = load_annotated_data(str(input_csv))
    
    if not data:
        logger.error("No valid data found to process.")
        sys.exit(1)
    
    metrics_to_bin = ['cc', 'halstead_volume', 'maintainability_index']
    all_boundaries = {}
    
    for metric in metrics_to_bin:
        logger.info(f"Calculating tertiles for {metric}")
        data, lower, upper = bin_complexity_metrics(data, metric)
        all_boundaries[metric] = {
            "low_max": lower,
            "medium_max": upper
        }
        logger.info(f"  {metric} boundaries: Low <= {lower:.4f}, Medium ({lower:.4f}, {upper:.4f}], High > {upper:.4f}")
    
    save_binned_data(data, str(output_csv))
    update_metadata(str(metadata_file), all_boundaries)
    
    logger.info("T017 Binning Strategy completed successfully.")

if __name__ == "__main__":
    main()
