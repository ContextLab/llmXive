"""
T022: Validate Sample Size for User Story 2.

Verifies that data/processed/cleaned_responses.csv meets the target N >= 100
valid responses (SC-002).

If insufficient, exits with code 1 and logs the specific error message.
If sufficient, logs success and exits with code 0.

This task also creates T022.1's requirement: a JSON report to
data/outputs/validation_report.json.
"""

import os
import sys
import json
import csv
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLEANED_RESPONSES_PATH = PROJECT_ROOT / "data" / "processed" / "cleaned_responses.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "outputs"
VALIDATION_REPORT_PATH = OUTPUT_DIR / "validation_report.json"

TARGET_N = 100


def load_cleaned_responses_count(file_path: Path) -> int:
    """
    Count the number of valid rows in the cleaned responses CSV.
    Assumes the file has a header row.
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return 0

    count = 0
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # Count rows
            for _ in reader:
                count += 1
    except Exception as e:
        logger.error(f"Error reading CSV: {e}")
        return 0

    return count


def save_validation_report(current_n: int, threshold: int, status: str, file_path: Path):
    """
    Save the validation report to a JSON file.
    """
    # Ensure output directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "current_n": current_n,
        "threshold": threshold,
        "status": status,
        "message": "PASS" if status == "PASS" else "FAIL"
    }

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Validation report saved to: {file_path}")


def main():
    logger.info(f"Starting sample size validation for {CLEANED_RESPONSES_PATH}")

    if not CLEANED_RESPONSES_PATH.exists():
        logger.error(f"Required file not found: {CLEANED_RESPONSES_PATH}")
        logger.error("Ensure T021 (cleaning) has been run successfully.")
        sys.exit(1)

    current_n = load_cleaned_responses_count(CLEANED_RESPONSES_PATH)
    logger.info(f"Current valid response count (N): {current_n}")

    status = "PASS" if current_n >= TARGET_N else "FAIL"

    # Save the report (T022.1 requirement)
    save_validation_report(current_n, TARGET_N, status, VALIDATION_REPORT_PATH)

    if current_n < TARGET_N:
        error_msg = f"ERROR: Insufficient sample size. N={current_n} < {TARGET_N} required for power analysis."
        logger.error(error_msg)
        sys.exit(1)
    else:
        success_msg = f"SUCCESS: Sample size target met. N={current_n} >= {TARGET_N}."
        logger.info(success_msg)
        sys.exit(0)


if __name__ == "__main__":
    main()
