"""
validate_metadata.py

Fatal gate script for Phase 0.

This script verifies that the required behavioral columns are present in the
downloaded metadata file (data/raw/metadata.csv). If any required column is
missing, it logs a fatal error message and exits with a non‑zero status,
preventing downstream pipeline steps from running.

Required columns:
  - pre_motor_score
  - post_motor_score
  - age
  - sex
  - subject_id
"""

import sys
import pandas as pd
from llmxive_toolkit import paths, get_logger

# Obtain a logger; it writes to stdout by default.
log = get_logger(__name__)

# Path to the metadata CSV produced by the download step (T001)
METADATA_PATH = paths.data("raw", "metadata.csv")

REQUIRED_COLUMNS = {
    "pre_motor_score",
    "post_motor_score",
    "age",
    "sex",
    "subject_id",
}

def verify_columns(df: pd.DataFrame) -> None:
    """Check for the presence of all required columns.

    Raises:
        SystemExit: If any required column is missing.
    """
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        log.error(
            "Fatal: Dataset lacks behavioral motor task metrics. "
            f"Missing columns: {', '.join(sorted(missing))}"
        )
        # Exit with a non‑zero status to signal a fatal gate failure.
        sys.exit(1)
    else:
        log.info("All required behavioral columns are present in metadata.")

def main() -> None:
    """Entry point for the fatal gate validation."""
    if not METADATA_PATH.is_file():
        log.error(f"Fatal: Metadata file not found at {METADATA_PATH}")
        sys.exit(1)

    try:
        df = pd.read_csv(METADATA_PATH)
    except Exception as exc:
        log.error(f"Fatal: Unable to read metadata CSV: {exc}")
        sys.exit(1)

    verify_columns(df)

    # Successful validation – downstream steps can proceed.
    log.info("Metadata validation passed. Pipeline may continue.")

if __name__ == "__main__":
    main()
