import os
import csv
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import yaml

from src.utils.config import get_project_root, get_interim_data_dir, get_processed_data_dir
from src.utils.logging import setup_logger

# Initialize logger
logger = setup_logger("preprocessing")

def load_csv(file_path: Path) -> List[Dict[str, str]]:
    """Load a CSV file into a list of dictionaries."""
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def save_csv(data: List[Dict[str, str]], file_path: Path) -> None:
    """Save a list of dictionaries to a CSV file."""
    if not data:
        logger.warning(f"No data to save to {file_path}")
        # Create empty file with headers if possible, or just touch it
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("")
        return

    fieldnames = data[0].keys()
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def validate_against_schema(data: List[Dict[str, str]], schema_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate data against a YAML schema definition.
    Returns (is_valid, list_of_errors).
    """
    if not schema_path.exists():
        logger.warning(f"Schema file not found: {schema_path}. Skipping validation.")
        return True, []

    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)

    errors = []
    required_fields = schema.get('required_fields', [])
    
    if not data:
        return True, []

    for i, row in enumerate(data):
        for field in required_fields:
            if field not in row or row[field] is None or row[field] == '':
                errors.append(f"Row {i}: Missing or empty required field '{field}'")
    
    return len(errors) == 0, errors

def combine_datasets(datasets: List[List[Dict[str, str]]]) -> List[Dict[str, str]]:
    """Combine multiple datasets into one."""
    combined = []
    for dataset in datasets:
        combined.extend(dataset)
    return combined

def filter_by_snr_threshold(input_path: Path, output_path: Path, 
                            dropped_path: Path, snr_threshold: float = 10.0) -> Tuple[int, int]:
    """
    Filter records based on SNR threshold.
    
    Args:
        input_path: Path to the input CSV (noise_mapped.csv or similar)
        output_path: Path to save filtered records
        dropped_path: Path to save dropped records
        snr_threshold: Minimum SNR in dB to keep a record (default 10.0)
    
    Returns:
        Tuple of (kept_count, dropped_count)
    
    This implements the core filtering logic for T017a.
    Records with SNR <= threshold are dropped.
    """
    logger.info(f"Starting SNR filtering with threshold {snr_threshold} dB")
    logger.info(f"Input: {input_path}, Output: {output_path}, Dropped: {dropped_path}")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    data = load_csv(input_path)
    
    kept_records = []
    dropped_records = []
    
    # Check if SNR column exists
    if not data:
        logger.warning("Input file is empty")
        save_csv([], output_path)
        save_csv([], dropped_path)
        return 0, 0
    
    if 'snr_db' not in data[0]:
        # Try alternative column names
        if 'snr' in data[0]:
            snr_col = 'snr'
        elif 'signal_noise_ratio' in data[0]:
            snr_col = 'signal_noise_ratio'
        else:
            raise ValueError("No SNR column found in input data. Expected 'snr_db', 'snr', or 'signal_noise_ratio'")
    else:
        snr_col = 'snr_db'
    
    for row in data:
        try:
            snr_value = float(row.get(snr_col, 0))
        except (ValueError, TypeError):
            # Invalid SNR value - drop the record
            dropped_records.append({**row, 'drop_reason': 'invalid_snr_value'})
            continue
        
        if snr_value > snr_threshold:
            kept_records.append(row)
        else:
            dropped_records.append({**row, 'drop_reason': f'snr_below_threshold_{snr_threshold}'})
    
    # Save results
    save_csv(kept_records, output_path)
    save_csv(dropped_records, dropped_path)
    
    logger.info(f"Filtering complete: {len(kept_records)} kept, {len(dropped_records)} dropped")
    return len(kept_records), len(dropped_records)

def run_sensitivity_analysis(input_path: Path, thresholds: List[float], 
                             output_dir: Path) -> Dict[float, Tuple[int, int]]:
    """
    Run filtering with multiple SNR thresholds for sensitivity analysis.
    
    Args:
        input_path: Path to input CSV
        thresholds: List of SNR thresholds to test
        output_dir: Directory to save results
    
    Returns:
        Dictionary mapping threshold -> (kept_count, dropped_count)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    
    for threshold in thresholds:
        output_file = output_dir / f"filtered_snr_threshold_{threshold}.csv"
        dropped_file = output_dir / f"dropped_snr_threshold_{threshold}.csv"
        
        kept, dropped = filter_by_snr_threshold(
            input_path, output_file, dropped_file, threshold
        )
        results[threshold] = (kept, dropped)
        logger.info(f"Threshold {threshold}: kept={kept}, dropped={dropped}")
    
    return results

def main():
    """
    Main entry point for the preprocessing module.
    Executes T017a: Filtering Engine with default SNR threshold.
    """
    root = get_project_root()
    interim_dir = get_interim_data_dir()
    
    # Input file from previous step (T015)
    input_file = interim_dir / "noise_mapped.csv"
    
    # Output files for T017a
    output_file = interim_dir / "filtered_snr.csv"
    dropped_file = interim_dir / "dropped_snr_filtered.csv"
    
    # Default threshold from project constraints (10 dB)
    default_threshold = 10.0
    
    try:
        kept_count, dropped_count = filter_by_snr_threshold(
            input_file, output_file, dropped_file, default_threshold
        )
        
        logger.info(f"T017a completed successfully.")
        logger.info(f"Output: {output_file} ({kept_count} records)")
        logger.info(f"Dropped: {dropped_file} ({dropped_count} records)")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Input file missing: {e}")
        return 1
    except Exception as e:
        logger.error(f"Filtering failed: {e}")
        raise

if __name__ == "__main__":
    exit(main())