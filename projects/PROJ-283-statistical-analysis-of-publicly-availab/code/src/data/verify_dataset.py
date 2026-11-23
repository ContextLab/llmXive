"""
Dataset Verification Script (T000)

This script checks that the raw chess dataset contains the required columns:
- white_rating
- black_rating
- eco_code
- move_times
- outcome

It writes a JSON verification report to ``data/results/dataset_verification.json`` with:
  {
    "all_columns_present": <bool>,
    "missing_columns": [<list of missing column names>]
  }

The script exits with status 0 if all required columns are present;
otherwise it exits with status 1 after writing the report.
"""

import sys
import json
import logging
from pathlib import Path

import pandas as pd

# llmxive_toolkit helpers for consistent project paths
from llmxive_toolkit import get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
REQUIRED_COLUMNS = {
    "white_rating",
    "black_rating",
    "eco_code",
    "move_times",
    "outcome",
}

# Use the current working directory as the project root for test isolation.
# This allows the script to be executed in a temporary directory (as done by the tests)
# while still supporting normal execution from the repository root.
PROJECT_ROOT = Path.cwd()

# Default raw data locations (the project may store the raw dump as Parquet or CSV)
RAW_DATA_CANDIDATES = [
    PROJECT_ROOT / "data" / "raw" / "games.parquet",
    PROJECT_ROOT / "data" / "raw" / "games.csv",
    PROJECT_ROOT / "data" / "raw" / "sample_games.parquet",
    PROJECT_ROOT / "data" / "raw" / "sample_games.csv",
]

# Output report location (as required by the task specification)
REPORT_PATH = PROJECT_ROOT / "data" / "results" / "dataset_verification.json"

# ----------------------------------------------------------------------
# Logger setup
# ----------------------------------------------------------------------
logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def locate_raw_dataset() -> Path | None:
    """
    Return the first existing raw dataset file from ``RAW_DATA_CANDIDATES``.
    If none exist, return ``None``.
    """
    for candidate in RAW_DATA_CANDIDATES:
        if candidate.exists():
            logger.info(f"Found raw dataset at {candidate}")
            return candidate
    logger.warning("No raw dataset file found among candidates.")
    return None

def load_raw_dataset(path: Path) -> pd.DataFrame:
    """
    Load a raw dataset file using pandas. Supports Parquet and CSV based on
    the file suffix.
    """
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"Unsupported raw dataset format: {path.suffix}")

def verify_columns(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """
    Check that all ``REQUIRED_COLUMNS`` are present in ``df``.
    Returns a tuple ``(all_present, missing_columns)``.
    """
    present = set(df.columns.astype(str))
    missing = sorted(REQUIRED_COLUMNS - present)
    all_present = len(missing) == 0
    return all_present, missing

def write_report(all_present: bool, missing: list[str]) -> None:
    """
    Write the JSON verification report to ``REPORT_PATH``.
    """
    report = {
        "all_columns_present": all_present,
        "missing_columns": missing,
    }
    # Ensure the results directory exists
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Verification report written to {REPORT_PATH}")

# ----------------------------------------------------------------------
# Main execution flow
# ----------------------------------------------------------------------
def main() -> int:
    raw_path = locate_raw_dataset()
    if raw_path is None:
        # No dataset – treat as failure but still produce a report
        write_report(False, ["file_not_found"])
        return 1

    try:
        df = load_raw_dataset(raw_path)
    except Exception as exc:
        logger.error(f"Failed to load raw dataset from {raw_path}: {exc}")
        write_report(False, ["load_error"])
        return 1

    all_present, missing = verify_columns(df)
    write_report(all_present, missing)

    if all_present:
        logger.info("All required columns are present.")
        return 0
    else:
        logger.error(f"Missing required columns: {', '.join(missing)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
