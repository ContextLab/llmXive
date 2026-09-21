import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

from utils import setup_logging, get_logger

# Required schema keys as per T008 specification
REQUIRED_KEYS = {"sample_size", "seed", "method", "total_rows_scanned"}
REQUIRED_TYPES = {
    "sample_size": int,
    "seed": int,
    "method": str,
    "total_rows_scanned": int
}

def load_sampling_log(log_path: Path) -> dict:
    """Load the sampling log JSON file."""
    if not log_path.exists():
        raise FileNotFoundError(f"Sampling log not found at {log_path}")
    
    with open(log_path, 'r') as f:
        return json.load(f)

def validate_schema(data: dict) -> tuple[bool, list[str]]:
    """
    Validate the sampling log schema against T008 requirements.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    
    # Check for missing keys
    missing_keys = REQUIRED_KEYS - set(data.keys())
    if missing_keys:
        errors.append(f"Missing required keys: {missing_keys}")
    
    # Check for extra keys (optional, but good to log)
    extra_keys = set(data.keys()) - REQUIRED_KEYS
    if extra_keys:
        logging.warning(f"Extra keys found in sampling log (ignoring): {extra_keys}")
    
    # Check types
    for key, expected_type in REQUIRED_TYPES.items():
        if key in data:
            if not isinstance(data[key], expected_type):
                errors.append(f"Key '{key}' has type {type(data[key]).__name__}, expected {expected_type.__name__}")
    
    # Specific business logic checks
    if "seed" in data and data["seed"] != 42:
        errors.append(f"Seed mismatch: expected 42, got {data['seed']}")
    
    if "method" in data and data["method"] != "streaming_islice":
        errors.append(f"Method mismatch: expected 'streaming_islice', got '{data['method']}'")
    
    if "sample_size" in data and data["sample_size"] <= 0:
        errors.append(f"Sample size must be positive, got {data['sample_size']}")
    
    if "total_rows_scanned" in data and data["total_rows_scanned"] < data.get("sample_size", 0):
        errors.append(f"Total rows scanned ({data['total_rows_scanned']}) cannot be less than sample size ({data['sample_size']})")
    
    return len(errors) == 0, errors

def write_review_report(report_path: Path, is_valid: bool, errors: list[str], data: dict) -> None:
    """Write the validation review report to disk."""
    timestamp = datetime.now().isoformat()
    
    lines = [
        "Sampling Log Validation Report",
        "=" * 40,
        f"Timestamp: {timestamp}",
        f"File Validated: {report_path.parent / 'sampling_log.json'}",
        f"Status: {'PASSED' if is_valid else 'FAILED'}",
        "",
        "Schema Validation:",
        "-" * 20,
    ]
    
    if is_valid:
        lines.append("All schema requirements met.")
        lines.append(f"- sample_size: {data.get('sample_size')}")
        lines.append(f"- seed: {data.get('seed')}")
        lines.append(f"- method: {data.get('method')}")
        lines.append(f"- total_rows_scanned: {data.get('total_rows_scanned')}")
    else:
        lines.append("Schema validation failed with the following errors:")
        for err in errors:
            lines.append(f"  - {err}")
    
    lines.append("")
    lines.append("Raw Data Content:")
    lines.append("-" * 20)
    lines.append(json.dumps(data, indent=2))
    
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        f.write("\n".join(lines) + "\n")

def main():
    """Main entry point for T046."""
    setup_logging()
    logger = get_logger(__name__)
    
    project_root = Path(__file__).parent.parent
    log_path = project_root / "data" / "processed" / "sampling_log.json"
    report_path = project_root / "data" / "processed" / "sampling_review.txt"
    
    logger.info(f"Starting sampling log verification for {log_path}")
    
    try:
        data = load_sampling_log(log_path)
        is_valid, errors = validate_schema(data)
        write_review_report(report_path, is_valid, errors, data)
        
        if is_valid:
            logger.info("Sampling log validation PASSED. Report written.")
            sys.exit(0)
        else:
            logger.error("Sampling log validation FAILED. Report written.")
            logger.error(f"Errors: {errors}")
            sys.exit(1)
            
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        # Write a failure report even if file is missing
        write_review_report(report_path, False, [str(e)], {})
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in sampling log: {e}")
        write_review_report(report_path, False, [f"JSON Decode Error: {e}"], {})
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        write_review_report(report_path, False, [f"Unexpected error: {e}"], {})
        sys.exit(1)

if __name__ == "__main__":
    main()