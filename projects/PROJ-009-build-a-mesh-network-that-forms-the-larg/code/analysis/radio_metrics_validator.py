"""
Radio Metrics Validator (T046b)

Validates that radio metrics were successfully extracted from the raw data.
Checks for the existence of data/raw/radio_metrics_extracted.json and ensures
that SNR and Bandwidth values are not null.

If validation fails, raises RadioMetricsMissingError to flag the run as 'WARN'
for downstream processing (T010a).
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

from orchestrator.logger import get_logger

# Configure logging for this module
logger = get_logger(__name__)

INPUT_FILE_PATH = "data/raw/radio_metrics_extracted.json"
VALIDATION_STATUS_PATH = "data/raw/validation_status.json"

class RadioMetricsMissingError(Exception):
    """Raised when required radio metrics are missing or null."""
    pass

def load_radio_metrics(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Loads the radio metrics extracted file.
    
    Args:
        file_path: Path to the JSON file.
        
    Returns:
        Dict containing metrics or None if file not found.
    """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"Radio metrics file not found: {file_path}")
        return None
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse radio metrics JSON: {e}")
        return None

def validate_metrics(metrics: Dict[str, Any]) -> bool:
    """
    Validates that critical radio metrics are present and not null.
    
    Args:
        metrics: Dictionary containing 'avg_snr_db', 'avg_bandwidth_Mbps', etc.
        
    Returns:
        True if valid, False otherwise.
    """
    critical_fields = ['avg_snr_db', 'avg_bandwidth_Mbps']
    
    for field in critical_fields:
        value = metrics.get(field)
        if value is None:
            logger.warning(f"Critical radio metric '{field}' is null or missing.")
            return False
        
        # Ensure it's a number
        if not isinstance(value, (int, float)):
            logger.warning(f"Critical radio metric '{field}' is not a number: {type(value)}")
            return False

    return True

def update_validation_status(status: str, reason: str, non_critical_missing: list = None):
    """
    Updates the global validation status file.
    
    Args:
        status: 'valid' or 'warn'.
        reason: Description of the validation outcome.
        non_critical_missing: List of non-critical fields missing (optional).
    """
    path = Path(VALIDATION_STATUS_PATH)
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing status if it exists
    data = {}
    if path.exists():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            data = {}
    
    # Update specific fields
    data['radio_metrics_status'] = status
    data['radio_metrics_reason'] = reason
    
    if non_critical_missing:
        current_nc = data.get('non_critical_missing', [])
        current_nc.extend(non_critical_missing)
        data['non_critical_missing'] = list(set(current_nc))
    
    # Write back
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Updated validation status: {status} - {reason}")

def validate_radio_metrics(input_path: str = INPUT_FILE_PATH) -> bool:
    """
    Main entry point to validate radio metrics.
    
    Args:
        input_path: Path to the radio metrics JSON file.
        
    Returns:
        True if validation passes, False otherwise.
        
    Raises:
        RadioMetricsMissingError: If metrics are missing or null.
    """
    logger.info(f"Validating radio metrics from {input_path}")
    
    metrics = load_radio_metrics(input_path)
    
    if metrics is None:
        msg = f"Radio metrics file missing or invalid: {input_path}"
        update_validation_status('warn', msg, non_critical_missing=['radio_metrics'])
        raise RadioMetricsMissingError(msg)
    
    if not validate_metrics(metrics):
        msg = "Radio metrics contain null or invalid critical values."
        update_validation_status('warn', msg, non_critical_missing=['snr_db', 'bandwidth_Mbps'])
        raise RadioMetricsMissingError(msg)
    
    logger.info("Radio metrics validation passed.")
    update_validation_status('valid', "Radio metrics present and valid.")
    return True

def main():
    """CLI entry point for validation."""
    import sys
    try:
        validate_radio_metrics()
        print("Radio metrics validation: PASSED")
        sys.exit(0)
    except RadioMetricsMissingError as e:
        print(f"Radio metrics validation: FAILED - {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error during validation")
        print(f"Radio metrics validation: ERROR - {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()