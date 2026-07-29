import os
import sys
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.logging import get_logger
from utils.config import get_data_path

logger = get_logger(__name__)

def verify_csv_artifact(
    filename: str,
    required_columns: Optional[List[str]] = None,
    min_rows: int = 1
) -> bool:
    """
    Verify that a CSV artifact exists, is readable, and meets structural constraints.

    Args:
        filename: Relative filename under data/processed/ or data/raw/
        required_columns: Optional list of columns that must be present.
        min_rows: Minimum number of data rows required (excluding header).

    Returns:
        True if verification passes, False otherwise.
    """
    data_path = get_data_path()
    file_path = data_path / filename

    if not file_path.exists():
        logger.error(f"Artifact missing: {file_path}")
        return False

    if not file_path.is_file():
        logger.error(f"Path is not a file: {file_path}")
        return False

    try:
        with open(file_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

            if headers is None:
                logger.error(f"CSV file {filename} is empty or has no header.")
                return False

            if required_columns:
                missing = set(required_columns) - set(headers)
                if missing:
                    logger.error(f"CSV {filename} missing required columns: {missing}")
                    return False

            row_count = 0
            for _ in reader:
                row_count += 1
                # Optional: could validate individual row types here if needed

            if row_count < min_rows:
                logger.error(
                    f"CSV {filename} has only {row_count} rows, "
                    f"minimum required is {min_rows}."
                )
                return False

            logger.info(
                f"CSV verification passed for {filename}: "
                f"{row_count} rows, columns: {list(headers)}"
            )
            return True

    except Exception as e:
        logger.error(f"Error reading CSV {filename}: {e}", exc_info=True)
        return False

def verify_log_artifact(
    filename: str,
    min_lines: int = 0,
    expected_patterns: Optional[List[str]] = None
) -> bool:
    """
    Verify that a log artifact exists and meets basic constraints.

    Args:
        filename: Relative filename under data/raw/
        min_lines: Minimum number of lines required.
        expected_patterns: Optional list of substrings that must appear at least once.

    Returns:
        True if verification passes, False otherwise.
    """
    data_path = get_data_path()
    file_path = data_path / filename

    if not file_path.exists():
        logger.error(f"Log artifact missing: {file_path}")
        return False

    if not file_path.is_file():
        logger.error(f"Path is not a file: {file_path}")
        return False

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if len(lines) < min_lines:
            logger.error(
                f"Log {filename} has {len(lines)} lines, "
                f"minimum required is {min_lines}."
            )
            return False

        content = "".join(lines)

        if expected_patterns:
            missing_patterns = [
                p for p in expected_patterns if p not in content
            ]
            if missing_patterns:
                logger.error(
                    f"Log {filename} missing expected patterns: {missing_patterns}"
                )
                return False

        logger.info(
            f"Log verification passed for {filename}: {len(lines)} lines"
        )
        return True

    except Exception as e:
        logger.error(f"Error reading log {filename}: {e}", exc_info=True)
        return False

def main() -> int:
    """
    Main entry point for T019: Verify and archive output.

    Verifies:
      - data/processed/cleaned_studies.csv
      - data/raw/excluded_studies.log

    Returns:
      0 if all verifications pass, 1 otherwise.
    """
    logger.info("Starting T019: Verify and archive output")

    # Define artifacts and their constraints
    csv_artifact = "processed/cleaned_studies.csv"
    log_artifact = "raw/excluded_studies.log"

    # Required columns based on the data model and pipeline design
    required_csv_columns = [
        "study_id",
        "title",
        "source",
        "population_age_min",
        "population_age_max",
        "diagnosis",
        "intervention_type",
        "delivery_format",
        "outcome_domain",
        "effect_size",
        "se_effect_size",
        "n_intervention",
        "n_control"
    ]

    # Log must at least exist and be non-empty if there were exclusions
    # We allow 0 lines if no studies were excluded, but the file must exist.
    # If the pipeline ran and excluded something, we expect at least some lines.
    # For robustness, we just check existence and readability; min_lines=0.
    log_min_lines = 0

    csv_ok = verify_csv_artifact(
        csv_artifact,
        required_columns=required_csv_columns,
        min_rows=1  # Expect at least one included study if pipeline ran
    )

    log_ok = verify_log_artifact(
        log_artifact,
        min_lines=log_min_lines
    )

    if csv_ok and log_ok:
        logger.info("T019 verification PASSED: all artifacts present and valid.")
        return 0
    else:
        logger.error("T019 verification FAILED: one or more artifacts invalid.")
        return 1

if __name__ == "__main__":
    sys.exit(main())