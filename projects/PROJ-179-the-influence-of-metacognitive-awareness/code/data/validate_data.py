"""
T006: Validate downloaded dataset for required behavioral fields.

Checks for the existence of 'confidence_rating' and 'source_label' columns
in the dataset downloaded by T005.

Output: data/validation_report.json
"""
import json
import logging
import os
import sys
import pandas as pd
from pathlib import Path

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Project root relative to this script's location
# Script is at code/data/validate_data.py, project root is parent of code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
REPORT_PATH = DATA_DIR / "validation_report.json"

REQUIRED_COLUMNS = ["confidence_rating", "source_label"]

def find_input_file():
    """
    Scan the raw data directory for a CSV file to validate.
    Returns the path to the first valid CSV found, or None.
    """
    if not RAW_DIR.exists():
        logger.error(f"Raw data directory not found: {RAW_DIR}")
        return None

    csv_files = list(RAW_DIR.glob("*.csv"))
    if not csv_files:
        logger.error("No CSV files found in raw data directory.")
        return None

    # Prefer the most recently modified file if multiple exist
    csv_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return csv_files[0]

def load_dataset(file_path: Path) -> pd.DataFrame:
    """
    Load the dataset from the given file path.
    """
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Successfully loaded dataset from {file_path}")
        logger.info(f"Dataset shape: {df.shape}")
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

def validate_fields(df: pd.DataFrame) -> bool:
    """
    Check if the dataframe contains the required columns.
    Raises ValueError if missing.
    """
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        error_msg = f"Required fields missing: {', '.join(missing)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("Validation passed: All required fields present.")
    return True

def write_report(status: str, details: str = None, file_path: Path = None):
    """
    Write the validation report to a JSON file.
    """
    if file_path is None:
        file_path = REPORT_PATH
    
    # Ensure output directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        "status": status,
        "timestamp": pd.Timestamp.now().isoformat(),
        "file_validated": str(RAW_DIR.glob("*.csv")) if RAW_DIR.exists() else "N/A",
        "details": details
    }
    
    with open(file_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report written to {file_path}")

def main():
    """
    Main entry point for T006.
    """
    logger.info("Starting data validation (T006)...")
    
    try:
        # 1. Find input file
        input_file = find_input_file()
        if input_file is None:
            write_report("FAIL", "No valid input dataset found in known locations.")
            sys.exit(1)

        # 2. Load dataset
        df = load_dataset(input_file)

        # 3. Validate fields
        validate_fields(df)

        # 4. Success
        write_report("PASS", "All required behavioral fields found.")
        sys.exit(0)

    except ValueError as e:
        write_report("FAIL", str(e))
        sys.exit(1)
    except Exception as e:
        write_report("FAIL", f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()