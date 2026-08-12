"""
Validation script for T099.
Verifies existence and schema compliance of baseline and cleaned metric artifacts.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils import setup_logging

# Paths relative to project root
BASELINE_METRICS_PATH = Path("data/processed/baseline_metrics.json")
CLEANED_METRICS_PATH = Path("data/processed/cleaned_metrics.json")

logger = setup_logging(log_level="INFO")


def validate_schema(data: Dict[str, Any], expected_keys: List[str], artifact_name: str) -> bool:
    """
    Validates that the data dictionary contains all expected keys.
    Returns True if valid, False otherwise.
    """
    missing_keys = [key for key in expected_keys if key not in data]
    if missing_keys:
        logger.error(f"{artifact_name} is missing required keys: {missing_keys}")
        return False
    
    # Check for non-empty values (no nulls, NaNs, or empty lists/dicts for critical fields)
    for key in expected_keys:
        value = data[key]
        if value is None:
            logger.error(f"{artifact_name} key '{key}' is None")
            return False
        if isinstance(value, (list, dict)) and len(value) == 0:
            logger.error(f"{artifact_name} key '{key}' is empty")
            return False
    
    return True


def validate_json_file(filepath: Path, required_keys: List[str], artifact_name: str) -> bool:
    """
    Loads a JSON file and validates its schema.
    Returns True if valid, False otherwise.
    """
    if not filepath.exists():
        logger.error(f"{artifact_name} file does not exist: {filepath}")
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"{artifact_name} file is not valid JSON: {e}")
        return False
    
    if not isinstance(data, dict):
        logger.error(f"{artifact_name} root element must be a dictionary, got {type(data)}")
        return False
    
    return validate_schema(data, required_keys, artifact_name)


def validate_baseline_metrics() -> bool:
    """
    Validates baseline_metrics.json.
    Expected keys: 'datasets' (list), 'metadata' (dict), 'timestamp' (str).
    """
    required_keys = ['datasets', 'metadata', 'timestamp']
    return validate_json_file(BASELINE_METRICS_PATH, required_keys, "Baseline metrics")


def validate_cleaned_metrics() -> bool:
    """
    Validates cleaned_metrics.json.
    Expected keys: 'datasets' (list), 'metadata' (dict), 'timestamp' (str).
    """
    required_keys = ['datasets', 'metadata', 'timestamp']
    return validate_json_file(CLEANED_METRICS_PATH, required_keys, "Cleaned metrics")


def main() -> int:
    """
    Main validation entry point.
    Returns 0 if all validations pass, 1 otherwise.
    """
    logger.info("Starting validation of metric artifacts...")
    
    baseline_valid = validate_baseline_metrics()
    cleaned_valid = validate_cleaned_metrics()
    
    if baseline_valid and cleaned_valid:
        logger.info("Validation PASSED: All artifacts exist and comply with schema.")
        return 0
    else:
        logger.error("Validation FAILED: One or more artifacts are missing or invalid.")
        if not baseline_valid:
            logger.error(f"  - {BASELINE_METRICS_PATH}")
        if not cleaned_valid:
            logger.error(f"  - {CLEANED_METRICS_PATH}")
        return 1


if __name__ == "__main__":
    sys.exit(main())