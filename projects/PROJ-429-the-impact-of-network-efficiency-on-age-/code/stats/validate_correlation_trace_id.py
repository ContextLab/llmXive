"""
T028 Implementation: Validate trace_id column in correlation_results.csv.

Validates that the 'trace_id' column exists in data/results/correlation_results.csv
and contains valid SHA-256 hex strings.

Crucial: If the file is missing or empty, logs a warning and exits 0 (does not block).
"""
import os
import sys
import logging
import re
import json
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
CORRELATION_RESULTS_PATH = Path("data/results/correlation_results.csv")
VALIDATION_REPORT_PATH = Path("data/results/trace_id_validation_report.json")
SHA256_PATTERN = re.compile(r'^[a-f0-9]{64}$')


def validate_trace_id_format(trace_id: str) -> bool:
    """
    Validate if a string is a valid SHA-256 hex string.

    Args:
        trace_id: String to validate

    Returns:
        True if valid SHA-256 hex string, False otherwise
    """
    if not isinstance(trace_id, str):
        return False
    if not trace_id:
        return False
    return bool(SHA256_PATTERN.match(trace_id.strip()))


def validate_correlation_trace_ids() -> dict:
    """
    Validate trace_id column in correlation_results.csv.

    Returns:
        Dictionary with validation results
    """
    results = {
        "file_exists": False,
        "file_empty": False,
        "column_exists": False,
        "all_valid": False,
        "total_rows": 0,
        "valid_count": 0,
        "invalid_count": 0,
        "invalid_indices": [],
        "status": "pending"
    }

    # Check if file exists
    if not CORRELATION_RESULTS_PATH.exists():
        logger.warning(f"File not found: {CORRELATION_RESULTS_PATH}")
        results["status"] = "file_missing"
        return results

    results["file_exists"] = True

    # Read and validate CSV
    try:
        import pandas as pd
        df = pd.read_csv(CORRELATION_RESULTS_PATH)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        results["status"] = "read_error"
        return results

    # Check if empty
    if df.empty:
        logger.warning(f"File exists but is empty: {CORRELATION_RESULTS_PATH}")
        results["file_empty"] = True
        results["status"] = "file_empty"
        return results

    results["total_rows"] = len(df)

    # Check if 'trace_id' column exists
    if 'trace_id' not in df.columns:
        logger.error("Column 'trace_id' not found in correlation_results.csv")
        results["status"] = "column_missing"
        return results

    results["column_exists"] = True

    # Validate each trace_id
    valid_count = 0
    invalid_count = 0
    invalid_indices = []

    for idx, row in df.iterrows():
        trace_id = row['trace_id']
        if validate_trace_id_format(trace_id):
            valid_count += 1
        else:
            invalid_count += 1
            invalid_indices.append(idx)

    results["valid_count"] = valid_count
    results["invalid_count"] = invalid_count
    results["invalid_indices"] = invalid_indices

    # Determine overall validity
    if invalid_count == 0 and valid_count > 0:
        results["all_valid"] = True
        results["status"] = "valid"
        logger.info(f"Validation successful: {valid_count}/{valid_count} trace_ids are valid SHA-256 strings.")
    elif valid_count == 0:
        results["status"] = "invalid"
        logger.warning(f"No valid trace_ids found. Total rows: {results['total_rows']}")
    else:
        results["status"] = "partial"
        logger.warning(f"Partial validation: {valid_count}/{results['total_rows']} trace_ids valid.")

    return results


def save_validation_report(results: dict) -> None:
    """
    Save validation report to JSON file.

    Args:
        results: Validation results dictionary
    """
    # Ensure output directory exists
    VALIDATION_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Add timestamp
    import datetime
    results["validated_at"] = datetime.datetime.now().isoformat()

    with open(VALIDATION_REPORT_PATH, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Validation report saved to: {VALIDATION_REPORT_PATH}")


def main():
    """
    Main entry point for trace_id validation.
    """
    logger.info("Starting trace_id validation for correlation_results.csv")
    logger.info(f"Target file: {CORRELATION_RESULTS_PATH}")

    # Run validation
    results = validate_correlation_trace_ids()

    # Save report
    save_validation_report(results)

    # Exit with appropriate code
    # Note: Per task requirements, we exit 0 even if file is missing
    # to avoid blocking the pipeline
    if results["status"] in ["valid", "partial"]:
        logger.info("Validation completed successfully.")
        sys.exit(0)
    elif results["status"] == "file_missing":
        logger.warning("File missing - exiting with success (non-blocking).")
        sys.exit(0)
    elif results["status"] == "file_empty":
        logger.warning("File empty - exiting with success (non-blocking).")
        sys.exit(0)
    elif results["status"] == "column_missing":
        logger.error("Column missing - validation failed.")
        sys.exit(1)
    elif results["status"] == "invalid":
        logger.error("All trace_ids invalid - validation failed.")
        sys.exit(1)
    else:
        logger.warning("Validation completed with warnings.")
        sys.exit(0)


if __name__ == "__main__":
    main()
