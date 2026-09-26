"""
Task T014a: Calculate Composition Validation Metrics.

Reads raw data files, excluded records, and cleaned data to calculate
the proportion of records that met the composition sum threshold (>=95%)
relative to the original raw dataset.

Output: data/processed/validation_metrics.yaml
"""
import os
import sys
import logging
import csv
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_composition_sum_threshold, get_data_raw_dir, get_data_processed_dir
from utils.logging_config import get_logger

logger = get_logger(__name__)

def count_raw_records(raw_dir: Path) -> int:
    """
    Count total records across all raw data files in the raw directory.
    Handles .csv and .json files.
    """
    total_count = 0
    raw_files = list(raw_dir.glob("raw_*"))
    
    if not raw_files:
        logger.warning(f"No raw files found in {raw_dir}")
        return 0

    for file_path in raw_files:
        try:
            if file_path.suffix == '.csv':
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    count = sum(1 for _ in reader)
                    logger.info(f"Counted {count} records in {file_path.name}")
                    total_count += count
            elif file_path.suffix == '.json':
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Handle list of dicts or dict with a specific key
                    if isinstance(data, list):
                        count = len(data)
                    elif isinstance(data, dict):
                        # Try to find a list value
                        count = next((len(v) for v in data.values() if isinstance(v, list)), 0)
                    else:
                        count = 0
                    logger.info(f"Counted {count} records in {file_path.name}")
                    total_count += count
            else:
                logger.debug(f"Skipping non-data file: {file_path.name}")
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            # Continue with other files

    return total_count

def get_excluded_count(excluded_file: Path) -> int:
    """
    Count records in the excluded_records.csv file.
    These are records that failed the composition sum threshold.
    """
    if not excluded_file.exists():
        logger.warning(f"Excluded records file not found: {excluded_file}")
        return 0

    try:
        with open(excluded_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = sum(1 for _ in reader)
        logger.info(f"Found {count} excluded records")
        return count
    except Exception as e:
        logger.error(f"Error reading excluded records: {e}")
        return 0

def calculate_validation_metrics(
    total_raw: int,
    excluded_count: int
) -> Dict[str, Any]:
    """
    Calculate validation metrics based on raw and excluded counts.

    Formula:
      passed_threshold_count = total_raw - excluded_count
      failed_threshold_count = excluded_count
      pass_rate_percentage = (passed_threshold_count / total_raw) * 100
    """
    if total_raw == 0:
        logger.warning("Total raw records is 0, cannot calculate pass rate.")
        return {
            "total_raw_records": 0,
            "passed_threshold_count": 0,
            "failed_threshold_count": 0,
            "pass_rate_percentage": 0.0
        }

    passed_count = total_raw - excluded_count
    if passed_count < 0:
        logger.warning(f"Calculated passed count ({passed_count}) is negative. Setting to 0.")
        passed_count = 0
        excluded_count = total_raw # Ensure consistency

    pass_rate = (passed_count / total_raw) * 100

    return {
        "total_raw_records": total_raw,
        "passed_threshold_count": passed_count,
        "failed_threshold_count": excluded_count,
        "pass_rate_percentage": round(pass_rate, 2)
    }

def save_metrics(metrics: Dict[str, Any], output_path: Path) -> None:
    """
    Save metrics to a YAML file.
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(metrics, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Validation metrics saved to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save metrics: {e}")
        raise

def main() -> int:
    """
    Main entry point for T014a.
    """
    logger.info("Starting T014a: Calculate Composition Validation Metrics")

    # Paths
    raw_dir = get_data_raw_dir()
    processed_dir = get_data_processed_dir()
    excluded_file = processed_dir / "excluded_records.csv"
    output_file = processed_dir / "validation_metrics.yaml"

    # Ensure directories exist
    if not raw_dir.exists():
        logger.error(f"Raw data directory does not exist: {raw_dir}")
        return 1
    if not processed_dir.exists():
        logger.error(f"Processed data directory does not exist: {processed_dir}")
        return 1

    # 1. Count total raw records
    total_raw = count_raw_records(raw_dir)
    logger.info(f"Total raw records found: {total_raw}")

    # 2. Get excluded count
    excluded_count = get_excluded_count(excluded_file)
    logger.info(f"Excluded records count: {excluded_count}")

    # 3. Calculate metrics
    metrics = calculate_validation_metrics(total_raw, excluded_count)
    
    # Log summary
    logger.info(f"Validation Summary:")
    logger.info(f"  - Total Raw: {metrics['total_raw_records']}")
    logger.info(f"  - Passed Threshold: {metrics['passed_threshold_count']}")
    logger.info(f"  - Failed Threshold: {metrics['failed_threshold_count']}")
    logger.info(f"  - Pass Rate: {metrics['pass_rate_percentage']}%")

    # 4. Save metrics
    save_metrics(metrics, output_file)

    logger.info("T014a completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())