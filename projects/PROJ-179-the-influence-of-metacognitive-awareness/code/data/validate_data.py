"""
T006: Validate downloaded dataset for required behavioral fields.

Checks for the existence of 'confidence_rating' and 'source_label' columns
in the dataset produced by T005 (download.py).

Output:
    data/validation_report.json with status "PASS" or "FAIL".

Exit Codes:
    0: Validation passed.
    1: Validation failed (missing fields or file not found).
"""

import json
import logging
import os
import sys
import pandas as pd
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("code/data/validate_data.log", mode="w")
    ]
)
logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ["confidence_rating", "source_label"]
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPORT_PATH = DATA_DIR / "validation_report.json"

# Known potential input files from T005
POTENTIAL_INPUT_FILES = [
    DATA_DIR / "downloaded" / "behavioral_data.csv",
    DATA_DIR / "downloaded" / "ds003386_behavioral.csv",
    DATA_DIR / "behavioral_data.csv",
    DATA_DIR / "ds003386_behavioral.csv",
    DATA_DIR / "sample_behavioral_data.csv",
    DATA_DIR / "downloaded" / "sample_behavioral_data.csv",
]

def find_input_file():
    """
    Search for a valid input CSV file among known potential locations.
    Returns the Path to the first valid file found, or None.
    """
    logger.info("Searching for downloaded dataset...")
    for file_path in POTENTIAL_INPUT_FILES:
        if file_path.exists():
            logger.info(f"Found potential input file: {file_path}")
            # Quick check to ensure it's not empty
            try:
                pd.read_csv(file_path, nrows=1)
                return file_path
            except Exception as e:
                logger.warning(f"File {file_path} exists but is not a valid CSV: {e}")
    logger.error("No valid input dataset found in known locations.")
    return None

def load_dataset(file_path: Path) -> pd.DataFrame:
    """
    Load the dataset from the given file path.
    """
    logger.info(f"Loading dataset from {file_path}")
    try:
        # Try to infer delimiter, handle potential encoding issues
        df = pd.read_csv(file_path, encoding="utf-8")
        if df.empty:
            logger.error("Dataset is empty.")
            return None
        return df
    except pd.errors.EmptyDataError:
        logger.error("Dataset file is empty.")
        return None
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        return None

def validate_fields(df: pd.DataFrame) -> bool:
    """
    Check if the DataFrame contains the required columns.
    Raises ValueError if columns are missing.
    """
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        logger.error(f"Required fields missing: {', '.join(missing)}")
        raise ValueError(f"Required fields missing: {', '.join(missing)}")
    
    # Additional check: ensure columns are not all NaN
    for col in REQUIRED_COLUMNS:
        if df[col].isna().all():
            logger.error(f"Column '{col}' contains only NaN values.")
            raise ValueError(f"Required fields missing: {', '.join(missing)}")

    logger.info("All required fields present and valid.")
    return True

def write_report(status: str, message: str = ""):
    """
    Write the validation report to data/validation_report.json.
    """
    report = {
        "status": status,
        "message": message,
        "checked_columns": REQUIRED_COLUMNS,
        "report_path": str(REPORT_PATH)
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report written to {REPORT_PATH}")

def main():
    """
    Main entry point for T006.
    """
    try:
        # 1. Find input file
        input_file = find_input_file()
        if not input_file:
            write_report("FAIL", "No valid input dataset found.")
            sys.exit(1)

        # 2. Load dataset
        df = load_dataset(input_file)
        if df is None:
            write_report("FAIL", "Failed to load dataset.")
            sys.exit(1)

        # 3. Validate fields
        try:
            validate_fields(df)
            write_report("PASS", "Dataset validation successful.")
            logger.info("Validation PASSED.")
            sys.exit(0)
        except ValueError as e:
            write_report("FAIL", str(e))
            logger.error("Validation FAILED.")
            sys.exit(1)

    except Exception as e:
        logger.exception(f"Unexpected error during validation: {e}")
        write_report("FAIL", f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
