import os
import sys
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from utils import get_logger

logger = get_logger(__name__)

REQUIRED_KEYS = {
    "mae": (float, type(None)),
    "r2": (float, type(None)),
    "wilcoxon_p_value": (float, type(None)),
    "sc001_status": (str,),
    "collinearity_flags": (dict, type(None)),
    "redundancy_masks": (dict, type(None)),
    "power_status": (str, type(None)),
    "attribution_results": (dict, type(None)),
    "narrative_summary": (str, type(None)),
}

def load_json_file(path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its contents."""
    if not path.exists():
        logger.error(f"File not found: {path}")
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {path}: {e}")
        return None

def validate_metrics(data: Dict[str, Any]) -> bool:
    """
    Verify that metrics.json contains all required keys with valid data types.
    
    Returns True if valid, False otherwise.
    """
    valid = True
    for key, allowed_types in REQUIRED_KEYS.items():
        if key not in data:
            logger.error(f"Missing required key: '{key}'")
            valid = False
            continue
        
        value = data[key]
        # Check type against allowed types
        if not isinstance(value, allowed_types):
            logger.error(
                f"Key '{key}' has invalid type: {type(value).__name__}. "
                f"Expected one of: {[t.__name__ for t in allowed_types]}"
            )
            valid = False
        
        # Specific validation for sc001_status
        if key == "sc001_status":
            valid_values = {"PASS", "FAIL", "LOW_POWER", "computed_ground_truth"}
            if value not in valid_values:
                logger.error(
                    f"Key 'sc001_status' has invalid value: '{value}'. "
                    f"Expected one of: {valid_values}"
                )
                valid = False
    
    return valid

def main():
    """
    Verify data/processed/metrics.json contains all required keys and valid data types.
    
    Exit codes:
    0: Success - metrics.json is valid
    1: Failure - metrics.json is missing, invalid JSON, or missing/invalid keys
    """
    project_root = Path(__file__).resolve().parent.parent
    metrics_path = project_root / "data" / "processed" / "metrics.json"

    logger.info(f"Verifying metrics file: {metrics_path}")

    # Load file
    data = load_json_file(metrics_path)
    if data is None:
        logger.error("Failed to load metrics.json. Verification failed.")
        return 1

    # Validate structure
    if not validate_metrics(data):
        logger.error("Validation failed: metrics.json does not meet requirements.")
        return 1

    logger.info("Verification successful: metrics.json contains all required keys with valid types.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
