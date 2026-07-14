"""
Data validation script for the PROJ-179-the-influence-of-metacognitive-awareness project.

This script checks that the downloaded behavioral dataset contains the required
columns ``confidence_rating`` and ``source_label``.  It writes a JSON validation
report to ``data/validation_report.json`` and exits with status code 0 on success
or 1 on failure.

The public API of this module (as listed in the project specification) is:

    - log_info
    - log_error
    - find_csv_files
    - load_dataset
    - validate_fields
    - write_report
    - main
"""

import json
import logging
import sys
from pathlib import Path
from typing import List, Tuple

import pandas as pd

# --------------------------------------------------------------------------- #
# Logging helpers
# --------------------------------------------------------------------------- #
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


def log_info(message: str) -> None:
    """Convenient wrapper for ``logger.info`` used throughout the codebase."""
    logger.info(message)


def log_error(message: str) -> None:
    """Convenient wrapper for ``logger.error`` used throughout the codebase."""
    logger.error(message)


# --------------------------------------------------------------------------- #
# Core validation functions
# --------------------------------------------------------------------------- #
REQUIRED_FIELDS = {"confidence_rating", "source_label"}


def find_csv_files(raw_dir: Path) -> List[Path]:
    """
    Return a list of CSV files found in ``raw_dir`` (non‑recursive).

    Parameters
    ----------
    raw_dir: Path
        Directory that should contain the raw behavioural CSV(s).

    Returns
    -------
    List[Path]
        Paths to CSV files (may be empty).
    """
    if not raw_dir.is_dir():
        log_error(f"Raw data directory does not exist: {raw_dir}")
        return []
    csv_files = [p for p in raw_dir.iterdir() if p.is_file() and p.suffix.lower() == ".csv"]
    log_info(f"Found {len(csv_files)} CSV file(s) in {raw_dir}")
    return csv_files


def load_dataset(csv_path: Path) -> pd.DataFrame:
    """
    Load a CSV file into a pandas DataFrame.

    Parameters
    ----------
    csv_path: Path
        Path to the CSV file.

    Returns
    -------
    pd.DataFrame
    """
    try:
        df = pd.read_csv(csv_path)
        log_info(f"Loaded dataset with shape {df.shape} from {csv_path.name}")
        return df
    except Exception as exc:
        log_error(f"Failed to read CSV {csv_path}: {exc}")
        raise


def validate_fields(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Verify that ``df`` contains all required columns.

    Returns
    -------
    Tuple[bool, List[str]]
        (is_valid, missing_fields). ``is_valid`` is ``True`` when no required
        column is missing.
    """
    present = set(df.columns.str.lower())
    missing = [field for field in REQUIRED_FIELDS if field.lower() not in present]
    is_valid = len(missing) == 0
    if is_valid:
        log_info("All required fields are present.")
    else:
        log_error(f"Missing required fields: {missing}")
    return is_valid, missing


def write_report(report_path: Path, status: str, missing: List[str] | None = None) -> None:
    """
    Write a JSON validation report.

    Parameters
    ----------
    report_path: Path
        Destination path for the JSON report.
    status: str
        Either ``PASS`` or ``FAIL``.
    missing: list, optional
        List of missing fields (included only when status == ``FAIL``).
    """
    report = {"status": status}
    if missing:
        report["missing_fields"] = missing
    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("w", encoding="utf-8") as fp:
            json.dump(report, fp, indent=2)
        log_info(f"Validation report written to {report_path}")
    except Exception as exc:
        log_error(f"Failed to write validation report: {exc}")
        raise


# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    """
    Orchestrates the validation workflow.

    Expected directory layout (relative to the repository root):
        data/
            raw/          <- contains the downloaded CSV(s)
            validation_report.json  <- output
    """
    log_info("Starting data validation (T006)...")

    # Resolve the project root (two levels up from this file: code/data/validate_data.py)
    project_root = Path(__file__).resolve().parents[2]
    raw_dir = project_root / "data" / "raw"
    report_path = project_root / "data" / "validation_report.json"

    csv_files = find_csv_files(raw_dir)

    if not csv_files:
        log_error("No CSV files found in raw data directory.")
        write_report(report_path, status="FAIL", missing=list(REQUIRED_FIELDS))
        sys.exit(1)

    # For simplicity we validate the first CSV file found.
    dataset_path = csv_files[0]
    try:
        df = load_dataset(dataset_path)
    except Exception:
        write_report(report_path, status="FAIL", missing=list(REQUIRED_FIELDS))
        sys.exit(1)

    is_valid, missing = validate_fields(df)

    if is_valid:
        write_report(report_path, status="PASS")
        sys.exit(0)
    else:
        write_report(report_path, status="FAIL", missing=missing)
        sys.exit(1)


if __name__ == "__main__":
    main()