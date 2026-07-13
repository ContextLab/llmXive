"""
Task T006: Validate downloaded dataset for required behavioral fields.

Checks for the existence of 'confidence_rating' and 'source_label' columns
in the downloaded dataset. Outputs a validation report to data/validation_report.json.
"""
import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
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
    """
    possible_paths = [
        "data/behavioral_data.csv",
        "data/downloaded/behavioral_data.csv",
        "data/ds003386_behavioral.csv",
        "data/downloaded/ds003386_behavioral.csv",
        # Add the path used by download.py if it differs
        "data/sample_behavioral_data.csv"
    ]
    
    for path_str in possible_paths:
        full_path = Path(path_str)
        if full_path.exists():
            log_info(f"Found dataset at: {full_path}")
            try:
                df = pd.read_csv(full_path)
                return df, str(full_path)
            except Exception as e:
                log_error(f"Failed to read {full_path}: {e}")
                continue
    
    return None, None

def validate_fields(df):
    """
    Validate that the dataframe contains required columns.
    Raises ValueError if missing.
    """
    required_columns = ['confidence_rating', 'source_label']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        error_msg = f"Required fields missing: {', '.join(missing_columns)}"
        raise ValueError(error_msg)
    
    log_info("Validation passed: All required fields present.")
    return True

def write_report(status, message, file_path=None):
    """
    Write the validation report to data/validation_report.json.
    """
    report_dir = Path("data")
    report_dir.mkdir(exist_ok=True)
    report_path = report_dir / "validation_report.json"
    
    report = {
        "task_id": "T006",
        "status": status,
        "message": message,
        "dataset_path": file_path,
        "required_fields": ["confidence_rating", "source_label"],
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    log_info(f"Validation report written to {report_path}")

def main():
    log_info("Starting data validation (T006)...")
    
    try:
        df, file_path = load_dataset()
        
        if df is None:
            error_msg = "Could not find downloaded dataset. Expected one of: ['data/behavioral_data.csv', 'data/downloaded/behavioral_data.csv', 'data/ds003386_behavioral.csv', 'data/downloaded/ds003386_behavioral.csv']"
            log_error(error_msg)
            write_report("FAIL", error_msg)
            sys.exit(1)
        
        try:
            validate_fields(df)
            write_report("PASS", "Dataset validated successfully.", file_path)
            sys.exit(0)
        except ValueError as e:
            log_error(str(e))
            write_report("FAIL", str(e), file_path)
            sys.exit(1)
            
    except Exception as e:
        log_error(f"Unexpected error during validation: {e}")
        write_report("FAIL", f"Unexpected error: {str(e)}")
        sys.exit(1)
    
    # Validate fields
    is_valid, missing_fields = validate_fields(df)
    
    if not is_valid:
        report = {
            "status": "FAIL",
            "reason": f"Required fields missing: {', '.join(missing_fields)}",
            "missing_fields": missing_fields,
            "checked_fields": REQUIRED_FIELDS,
            "dataset_path": str(data_dir),
            "columns_found": list(df.columns)
        }
        write_report(report, output_path)
        raise ValueError(f"Required fields missing: {', '.join(missing_fields)}")
    
    # Success
    report = {
        "status": "PASS",
        "reason": "All required fields present",
        "missing_fields": [],
        "checked_fields": REQUIRED_FIELDS,
        "dataset_path": str(data_dir),
        "columns_found": list(df.columns),
        "row_count": len(df),
        "column_count": len(df.columns)
    }
    write_report(report, output_path)
    log_info("Validation passed. All required fields present.")
    sys.exit(0)

if __name__ == "__main__":
    main()