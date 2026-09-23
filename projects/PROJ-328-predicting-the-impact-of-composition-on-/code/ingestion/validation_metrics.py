"""
Module to calculate composition validation metrics.

This module reads raw data files, excluded records, and cleaned data to calculate
the proportion of records that met the composition sum threshold (≥95%) relative
to the original raw dataset.

Output: data/processed/validation_metrics.yaml
"""
import os
import sys
import logging
import csv
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from config import get_composition_sum_threshold, get_data_raw_dir, get_data_processed_dir
from utils.logging_config import get_logger

logger = get_logger(__name__)

def count_raw_records(raw_dir: Path) -> int:
    """
    Count total number of records in all raw data files.
    
    Args:
        raw_dir: Path to the raw data directory.
        
    Returns:
        Total count of records across all raw files.
    """
    total_count = 0
    raw_files = list(raw_dir.glob("*.csv")) + list(raw_dir.glob("*.json"))
    
    if not raw_files:
        logger.warning(f"No raw data files found in {raw_dir}")
        return 0
    
    for file_path in raw_files:
        try:
            if file_path.suffix == '.csv':
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    count = sum(1 for _ in reader)
                    total_count += count
                    logger.info(f"Counted {count} records from {file_path.name}")
            elif file_path.suffix == '.json':
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        count = len(data)
                        total_count += count
                        logger.info(f"Counted {count} records from {file_path.name}")
                    else:
                        logger.warning(f"JSON file {file_path.name} is not a list, skipping record count")
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            
    return total_count

def get_excluded_count(excluded_file: Path) -> int:
    """
    Count the number of excluded records from the excluded records file.
    
    Args:
        excluded_file: Path to the excluded records CSV file.
        
    Returns:
        Count of excluded records.
    """
    if not excluded_file.exists():
        logger.warning(f"Excluded records file not found: {excluded_file}")
        return 0
    
    try:
        with open(excluded_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = sum(1 for _ in reader)
            logger.info(f"Found {count} excluded records in {excluded_file.name}")
            return count
    except Exception as e:
        logger.error(f"Error reading excluded records file {excluded_file}: {e}")
        return 0

def calculate_validation_metrics(
    raw_dir: Path,
    excluded_file: Path,
    cleaned_file: Path,
    composition_threshold: float
) -> Dict[str, Any]:
    """
    Calculate validation metrics for composition sum threshold.
    
    Args:
        raw_dir: Path to raw data directory.
        excluded_file: Path to excluded records CSV.
        cleaned_file: Path to cleaned data CSV.
        composition_threshold: Threshold for composition sum (e.g., 95.0).
        
    Returns:
        Dictionary with validation metrics.
    """
    total_raw_records = count_raw_records(raw_dir)
    failed_threshold_count = get_excluded_count(excluded_file)
    
    if total_raw_records == 0:
        logger.warning("Total raw records is 0, cannot calculate metrics")
        return {
            "total_raw_records": 0,
            "passed_threshold_count": 0,
            "failed_threshold_count": 0,
            "pass_rate_percentage": 0.0,
            "error": "No raw records found"
        }
    
    passed_threshold_count = total_raw_records - failed_threshold_count
    
    if passed_threshold_count < 0:
        logger.warning(f"Passed count ({passed_threshold_count}) is negative, setting to 0")
        passed_threshold_count = 0
        failed_threshold_count = total_raw_records
    
    pass_rate_percentage = (passed_threshold_count / total_raw_records) * 100 if total_raw_records > 0 else 0.0
    
    metrics = {
        "total_raw_records": total_raw_records,
        "passed_threshold_count": passed_threshold_count,
        "failed_threshold_count": failed_threshold_count,
        "pass_rate_percentage": round(pass_rate_percentage, 2),
        "composition_threshold": composition_threshold
    }
    
    logger.info(f"Validation metrics calculated: {metrics}")
    return metrics

def save_metrics(metrics: Dict[str, Any], output_path: Path) -> None:
    """
    Save validation metrics to a YAML file.
    
    Args:
        metrics: Dictionary with metrics.
        output_path: Path to output YAML file.
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(metrics, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Validation metrics saved to {output_path}")
    except Exception as e:
        logger.error(f"Error saving metrics to {output_path}: {e}")
        raise

def main() -> None:
    """Main entry point for validation metrics calculation."""
    logger.info("Starting validation metrics calculation")
    
    raw_dir = get_data_raw_dir()
    processed_dir = get_data_processed_dir()
    
    excluded_file = processed_dir / "excluded_records.csv"
    cleaned_file = processed_dir / "solder_hardness_cleaned.csv"
    output_file = processed_dir / "validation_metrics.yaml"
    
    composition_threshold = get_composition_sum_threshold()
    
    logger.info(f"Raw directory: {raw_dir}")
    logger.info(f"Excluded file: {excluded_file}")
    logger.info(f"Cleaned file: {cleaned_file}")
    logger.info(f"Output file: {output_file}")
    logger.info(f"Composition threshold: {composition_threshold}")
    
    if not raw_dir.exists():
        logger.error(f"Raw directory does not exist: {raw_dir}")
        sys.exit(1)
        
    if not cleaned_file.exists():
        logger.error(f"Cleaned data file does not exist: {cleaned_file}")
        logger.error("Please run T013 (cleaner.py) before running this task.")
        sys.exit(1)
    
    metrics = calculate_validation_metrics(
        raw_dir=raw_dir,
        excluded_file=excluded_file,
        cleaned_file=cleaned_file,
        composition_threshold=composition_threshold
    )
    
    save_metrics(metrics, output_file)
    
    logger.info("Validation metrics calculation completed successfully")

if __name__ == "__main__":
    main()