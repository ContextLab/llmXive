import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path

# Configure logging for this module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def log_info(msg):
    logger.info(msg)

def log_error(msg):
    logger.error(msg)

def load_dataset():
    """
    Locate and load the downloaded dataset.
    Checks common paths where T005 might have saved the file.
    Returns the DataFrame if found, otherwise raises FileNotFoundError.
    """
    possible_paths = [
        Path("data/behavioral_data.csv"),
        Path("data/downloaded/behavioral_data.csv"),
        Path("data/ds003386_behavioral.csv"),
        Path("data/downloaded/ds003386_behavioral.csv"),
        Path("data/sample_behavioral_data.csv"),
        Path("data/downloaded/sample_behavioral_data.csv"),
        # Absolute paths relative to project root if running from code/
        Path("projects/PROJ-179-the-influence-of-metacognitive-awareness/data/behavioral_data.csv"),
        Path("projects/PROJ-179-the-influence-of-metacognitive-awareness/data/downloaded/behavioral_data.csv"),
    ]

    for p in possible_paths:
        if p.exists():
            log_info(f"Found dataset at: {p}")
            try:
                df = pd.read_csv(p)
                return df
            except Exception as e:
                log_error(f"Failed to read {p}: {e}")
                continue

    raise FileNotFoundError(
        "Could not find downloaded dataset. Ensure T005 (download) has completed successfully. "
        "Searched paths: " + ", ".join(str(p) for p in possible_paths)
    )

def validate_fields(df):
    """
    Check for required behavioral fields: 'confidence_rating' and 'source_label'.
    Raises ValueError if missing.
    Returns True if valid.
    """
    required_fields = ['confidence_rating', 'source_label']
    missing_fields = [f for f in required_fields if f not in df.columns]

    if missing_fields:
        error_msg = f"Required fields missing: {', '.join(missing_fields)}"
        log_error(error_msg)
        raise ValueError(error_msg)

    log_info("All required fields present.")
    return True

def write_report(status, message=""):
    """
    Write the validation report to data/validation_report.json.
    """
    report_path = Path("data/validation_report.json")
    # Ensure data directory exists
    report_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "status": status,
        "message": message,
        "task_id": "T006"
    }

    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    log_info(f"Validation report written to {report_path}")
    return report_path

def main():
    """
    Main entry point for T006: Validate downloaded data.
    """
    log_info("Starting data validation (T006)...")
    
    try:
        # 1. Load dataset
        df = load_dataset()
        log_info(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns.")

        # 2. Validate fields
        validate_fields(df)

        # 3. Write success report
        write_report("PASS", "All required fields found.")
        log_info("Validation successful.")
        sys.exit(0)

    except FileNotFoundError as e:
        log_error(str(e))
        write_report("FAIL", str(e))
        sys.exit(1)
    except ValueError as e:
        log_error(str(e))
        write_report("FAIL", str(e))
        sys.exit(1)
    except Exception as e:
        log_error(f"Unexpected error during validation: {e}")
        write_report("FAIL", f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()