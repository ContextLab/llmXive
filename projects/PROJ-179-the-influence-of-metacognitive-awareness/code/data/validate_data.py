import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path

# Configure logging to stderr to avoid file dependency issues if not set up
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Required fields as per task specification
REQUIRED_FIELDS = ['confidence_rating', 'source_label']

def log_info(msg: str):
    logger.info(msg)

def log_error(msg: str):
    logger.error(msg)

def load_dataset() -> pd.DataFrame:
    """
    Locate and load the downloaded dataset.
    Checks common paths where T005 might have saved the file.
    """
    possible_paths = [
        Path("data/behavioral_data.csv"),
        Path("data/downloaded/behavioral_data.csv"),
        Path("data/ds003386_behavioral.csv"),
        Path("data/downloaded/ds003386_behavioral.csv"),
        # Check for the sample data file if download succeeded there
        Path("data/sample_behavioral_data.csv"),
        Path("data/downloaded/sample_behavioral_data.csv")
    ]

    for p in possible_paths:
        if p.exists():
            log_info(f"Found dataset at: {p}")
            try:
                return pd.read_csv(p)
            except Exception as e:
                log_error(f"Failed to read {p}: {e}")
                continue

    log_error("Could not find downloaded dataset. Expected one of: " + str([str(p) for p in possible_paths]))
    return None

def validate_fields(df: pd.DataFrame) -> bool:
    """
    Check for required behavioral fields: confidence_rating, source_label.
    Raises ValueError and returns False if missing.
    """
    missing = [f for f in REQUIRED_FIELDS if f not in df.columns]
    if missing:
        err_msg = f"Required fields missing: {', '.join(missing)}"
        log_error(err_msg)
        raise ValueError(err_msg)
    
    log_info("Validation passed: All required fields present.")
    return True

def write_report(status: str, message: str, path: Path):
    """
    Write the validation report to JSON.
    """
    report = {
        "status": status,
        "message": message
    }
    try:
        with open(path, 'w') as f:
            json.dump(report, f, indent=2)
        log_info(f"Validation report written to {path}")
    except Exception as e:
        log_error(f"Failed to write report: {e}")

def main():
    log_info("Starting data validation (T006)...")
    
    # 1. Load Dataset
    df = load_dataset()
    if df is None:
        # If no data found, we cannot validate fields. 
        # Report as FAIL to block downstream tasks.
        write_report("FAIL", "ERROR: No dataset found to validate.", Path("data/validation_report.json"))
        sys.exit(1)

    # 2. Validate Fields
    try:
        validate_fields(df)
        # Success
        write_report("PASS", "Validation successful. Required fields present.", Path("data/validation_report.json"))
        log_info("Validation completed successfully.")
        sys.exit(0)
    except ValueError as e:
        # Field missing - specific error
        write_report("FAIL", str(e), Path("data/validation_report.json"))
        sys.exit(1)
    except Exception as e:
        # Unexpected error
        write_report("FAIL", f"Unexpected error during validation: {str(e)}", Path("data/validation_report.json"))
        sys.exit(1)

if __name__ == "__main__":
    main()