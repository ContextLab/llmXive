import csv
import sys
import logging
from pathlib import Path
from typing import List, Set

from utils.logging import get_logger

REQUIRED_COLUMNS: Set[str] = {
    "snippet_id",
    "repo_url",
    "file_path",
    "median_commit_age",
    "snippet_content",
    "token_count",
    "complexity",
    "token_length",
}

MIN_ROW_COUNT: int = 800

def verify_csv_structure(
    csv_path: Path, required_columns: Set[str] = REQUIRED_COLUMNS, min_rows: int = MIN_ROW_COUNT
) -> bool:
    """
    Verify that the extraction output CSV exists, has the required columns,
    and contains at least the minimum number of rows.

    Returns True if all checks pass, False otherwise.
    """
    logger = get_logger(__name__)

    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        return False

    try:
        with open(csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            headers = set(reader.fieldnames or [])

            missing = required_columns - headers
            if missing:
                logger.error(f"Missing required columns: {sorted(missing)}")
                return False

            row_count = 0
            for row in reader:
                row_count += 1
                # Optional: validate non-null critical fields on first few rows
                if row_count <= 5:
                    if not row.get("snippet_id") or not row.get("snippet_content"):
                        logger.warning(f"Row {row_count} has missing critical fields")
                        # Not failing here, just logging

            if row_count < min_rows:
                logger.error(f"Row count {row_count} is below minimum {min_rows}")
                return False

            logger.info(f"Verification passed: {csv_path} has {row_count} rows and all required columns.")
            return True

    except Exception as e:
        logger.exception(f"Error reading CSV: {e}")
        return False

def main() -> int:
    """CLI entry point for verifying extraction output."""
    logger = get_logger(__name__)

    csv_path = Path("data/extracted/snippets.csv")

    if not csv_path.exists():
        logger.error(f"Extraction output not found at {csv_path}. "
                     "Please run code/extraction/run_extraction.py first.")
        return 1

    success = verify_csv_structure(csv_path)

    if not success:
        logger.error("Extraction output verification FAILED.")
        return 1

    logger.info("Extraction output verification PASSED.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
