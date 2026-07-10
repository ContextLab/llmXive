import os
import sys
import json
import logging
import csv
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Import logging configuration from existing utility
from utils.logging_config import setup_deterministic_logging, get_logger

# Constants
METRICS = ['cyclomatic_complexity', 'halstead_volume', 'maintainability_index']
BINS = ['Low', 'Medium', 'High']
METADATA_PATH = Path("data/processed/metadata.json")
ANNOTATED_CSV_PATH = Path("data/processed/annotated_metrics.csv")
BINNED_CSV_PATH = Path("data/processed/binned_metrics.csv")

def load_annotated_data(csv_path: Path) -> List[Dict[str, Any]]:
    """Load the annotated metrics CSV."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Required input file not found: {csv_path}")
    
    data = []
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert complexity metrics to float
            for metric in METRICS:
                if metric in row:
                    try:
                        row[metric] = float(row[metric])
                    except (ValueError, TypeError):
                        row[metric] = float('nan')
            data.append(row)
    return data

def calculate_tertiles(values: List[float]) -> Tuple[float, float]:
    """
    Calculate tertile boundaries (33.33% and 66.66% percentiles).
    Returns (lower_bound, upper_bound).
    Values < lower_bound -> Low
    Values >= lower_bound and < upper_bound -> Medium
    Values >= upper_bound -> High
    """
    # Filter out NaN values
    clean_values = [v for v in values if not (isinstance(v, float) and v != v)]
    
    if len(clean_values) == 0:
        return (0.0, 0.0)
    
    sorted_values = sorted(clean_values)
    n = len(sorted_values)
    
    # Calculate indices for tertiles
    idx_lower = int(n * 1/3)
    idx_upper = int(n * 2/3)
    
    # Ensure indices are within bounds
    idx_lower = max(0, min(idx_lower, n - 1))
    idx_upper = max(0, min(idx_upper, n - 1))
    
    # Handle edge cases where indices might be the same
    if idx_lower == idx_upper:
        # If all values are the same or very few, use the value itself
        return (sorted_values[idx_lower], sorted_values[idx_upper])
    
    lower_bound = sorted_values[idx_lower]
    upper_bound = sorted_values[idx_upper]
    
    return (lower_bound, upper_bound)

def assign_bin(value: float, lower: float, upper: float) -> str:
    """Assign a bin category based on value and boundaries."""
    if value != value:  # NaN check
        return "Unknown"
    
    if value < lower:
        return "Low"
    elif value < upper:
        return "Medium"
    else:
        return "High"

def bin_complexity_metrics(data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Tuple[float, float]]]:
    """
    Add bin columns for each metric and return the bin boundaries.
    """
    boundaries = {}
    
    for metric in METRICS:
        values = [row[metric] for row in data if metric in row]
        lower, upper = calculate_tertiles(values)
        boundaries[metric] = (lower, upper)
        
        # Assign bins to each row
        for row in data:
            if metric in row:
                row[f'{metric}_bin'] = assign_bin(row[metric], lower, upper)
            else:
                row[f'{metric}_bin'] = "Unknown"
    
    return data, boundaries

def save_binned_data(data: List[Dict[str, Any]], output_path: Path):
    """Save the binned data to a new CSV file."""
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not data:
        # Create empty file with headers if no data
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            pass
        return

    # Determine all fieldnames (original + new bin columns)
    fieldnames = list(data[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def update_metadata(boundaries: Dict[str, Tuple[float, float]], metadata_path: Path):
    """Update metadata.json with binning boundaries."""
    if not metadata_path.parent.exists():
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
    
    metadata = {}
    if metadata_path.exists():
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    
    # Add binning strategy info
    metadata['binning_strategy'] = {
        'type': 'tertiles',
        'bins': BINS,
        'boundaries': {
            metric: {
                'lower': float(bound[0]),
                'upper': float(bound[1])
            }
            for metric, bound in boundaries.items()
        }
    }
    
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

def main():
    """Main entry point for the binning task."""
    # Setup logging
    logger = setup_deterministic_logging()
    logger.info("Starting T017: Binning Strategy Implementation")
    
    try:
        # Load data
        logger.info(f"Loading annotated data from {ANNOTATED_CSV_PATH}")
        data = load_annotated_data(ANNOTATED_CSV_PATH)
        logger.info(f"Loaded {len(data)} snippets")
        
        if len(data) == 0:
            logger.warning("No data found to bin. Creating empty output.")
            save_binned_data([], BINNED_CSV_PATH)
            update_metadata({}, METADATA_PATH)
            return
        
        # Calculate bins
        logger.info("Calculating tertile boundaries for complexity metrics")
        binned_data, boundaries = bin_complexity_metrics(data)
        
        # Log boundaries
        for metric, (lower, upper) in boundaries.items():
            logger.info(f"{metric}: Low < {lower:.4f}, Medium [{lower:.4f}, {upper:.4f}), High >= {upper:.4f}")
        
        # Save binned data
        logger.info(f"Saving binned data to {BINNED_CSV_PATH}")
        save_binned_data(binned_data, BINNED_CSV_PATH)
        
        # Update metadata
        logger.info(f"Updating metadata at {METADATA_PATH}")
        update_metadata(boundaries, METADATA_PATH)
        
        logger.info("T017 completed successfully")
        
    except Exception as e:
        logger.error(f"Error during binning: {str(e)}")
        raise

if __name__ == "__main__":
    main()
