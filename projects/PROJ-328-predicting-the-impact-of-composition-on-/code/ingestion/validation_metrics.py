"""
T014a: Calculate Composition Validation Metrics.

Reads raw data and excluded records to calculate the proportion of records
that met the composition sum threshold (>=95%) relative to the original raw dataset.
"""
import os
import sys
import csv
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from config import (
    get_data_raw_dir,
    get_data_processed_dir,
    get_composition_sum_threshold,
    get_max_elements
)
from utils.logger import get_logger

logger = get_logger(__name__)

def count_raw_records() -> int:
    """
    Count total records in the raw data files.
    Looks for api_fetched.json (parsed as list of dicts) and literature_scraped.csv.
    Returns the sum of records found.
    """
    raw_dir = get_data_raw_dir()
    total_count = 0

    # Check for API fetched data (JSON)
    api_file = raw_dir / "api_fetched.json"
    if api_file.exists():
        try:
            import json
            with open(api_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    total_count += len(data)
                    logger.info(f"Found {len(data)} records in {api_file.name}")
                else:
                    logger.warning(f"{api_file.name} is not a list, skipping count")
        except Exception as e:
            logger.error(f"Error reading {api_file}: {e}")

    # Check for literature scraped data (CSV)
    csv_file = raw_dir / "literature_scraped.csv"
    if csv_file.exists():
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = sum(1 for _ in reader)
                total_count += count
                logger.info(f"Found {count} records in {csv_file.name}")
        except Exception as e:
            logger.error(f"Error reading {csv_file}: {e}")

    # Check for filtered_raw.csv if it exists (sometimes used as the consolidated raw)
    filtered_file = raw_dir / "filtered_raw.csv"
    if filtered_file.exists() and total_count == 0:
        # If no other raw files, assume filtered_raw is the source of truth for "raw" in this context
        # or if filtered_raw exists alongside others, we might need to decide.
        # Based on T012g, filtered_raw is a filtered version.
        # We strictly count from the *original* raw sources (api_fetched, literature_scraped).
        # If those don't exist but filtered_raw does, we might have a pipeline state issue,
        # but we count what we can find.
        try:
            with open(filtered_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = sum(1 for _ in reader)
                # Only add if we haven't found others, to avoid double counting if logic changes
                if total_count == 0:
                    total_count += count
                    logger.info(f"Found {count} records in {filtered_file.name} (fallback)")
        except Exception as e:
            logger.error(f"Error reading {filtered_file}: {e}")

    return total_count

def get_excluded_count() -> int:
    """
    Count records in the excluded_records.csv produced by T013.
    """
    processed_dir = get_data_processed_dir()
    excluded_file = processed_dir / "excluded_records.csv"

    if not excluded_file.exists():
        logger.warning(f"{excluded_file.name} not found. Assuming 0 excluded.")
        return 0

    try:
        with open(excluded_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = sum(1 for _ in reader)
            logger.info(f"Found {count} excluded records in {excluded_file.name}")
            return count
    except Exception as e:
        logger.error(f"Error reading {excluded_file}: {e}")
        return 0

def calculate_validation_metrics() -> Dict[str, Any]:
    """
    Calculate validation metrics based on raw count and excluded count.
    Returns a dictionary with:
      - total_raw_records: int
      - passed_threshold_count: int
      - failed_threshold_count: int (same as excluded_count)
      - pass_rate_percentage: float
    """
    total_raw = count_raw_records()
    failed_threshold = get_excluded_count()

    if total_raw == 0:
        logger.warning("Total raw records is 0. Cannot calculate pass rate.")
        return {
            "total_raw_records": 0,
            "passed_threshold_count": 0,
            "failed_threshold_count": 0,
            "pass_rate_percentage": 0.0
        }

    passed_threshold = total_raw - failed_threshold
    # Ensure passed is not negative (sanity check)
    if passed_threshold < 0:
        passed_threshold = 0
        logger.warning("Calculated passed threshold is negative. Clamping to 0.")

    pass_rate = (passed_threshold / total_raw) * 100.0

    return {
        "total_raw_records": total_raw,
        "passed_threshold_count": passed_threshold,
        "failed_threshold_count": failed_threshold,
        "pass_rate_percentage": round(pass_rate, 2)
    }

def save_metrics(metrics: Dict[str, Any], output_path: Optional[Path] = None):
    """
    Save metrics to YAML file.
    """
    if output_path is None:
        processed_dir = get_data_processed_dir()
        output_path = processed_dir / "validation_metrics.yaml"

    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(metrics, f, default_flow_style=False, sort_keys=False)
    logger.info(f"Saved validation metrics to {output_path}")

def main():
    """
    Entry point for T014a.
    """
    logger.info("Starting T014a: Calculate Composition Validation Metrics")

    try:
        metrics = calculate_validation_metrics()
        save_metrics(metrics)
        logger.info("T014a completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"T014a failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
