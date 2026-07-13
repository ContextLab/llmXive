"""
Task T006: Validate downloaded dataset for required behavioral fields.

Checks for the existence of 'confidence_rating' and 'source_label' columns
in the downloaded dataset and generates a validation report.
"""
import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Required fields
REQUIRED_FIELDS = ['confidence_rating', 'source_label']

def log_info(message):
    logger.info(message)

def log_error(message):
    logger.error(message)

def load_dataset(data_dir):
    """
    Attempt to load the dataset from expected locations.
    
    Args:
        data_dir: Path to the data directory
        
    Returns:
        pd.DataFrame or None if no valid dataset found
    """
    expected_files = [
        data_dir / 'behavioral_data.csv',
        data_dir / 'ds003386_behavioral.csv',
        data_dir / 'downloaded' / 'ds003386_behavioral.csv',
        data_dir / 'downloaded' / 'behavioral_data.csv'
    ]
    
    for file_path in expected_files:
        if file_path.exists():
            log_info(f"Found dataset at: {file_path}")
            try:
                df = pd.read_csv(file_path)
                return df
            except Exception as e:
                log_error(f"Failed to load {file_path}: {e}")
                continue
    
    log_error("Could not find downloaded dataset.")
    return None

def validate_fields(df):
    """
    Validate that required fields are present in the dataset.
    
    Args:
        df: pandas DataFrame
        
    Returns:
        tuple: (is_valid, missing_fields)
    """
    missing_fields = []
    for field in REQUIRED_FIELDS:
        if field not in df.columns:
            missing_fields.append(field)
    
    if missing_fields:
        return False, missing_fields
    return True, []

def write_report(report_data, output_path):
    """
    Write validation report to JSON file.
    
    Args:
        report_data: Dictionary containing report data
        output_path: Path to output file
    """
    with open(output_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    log_info(f"Validation report written to {output_path}")

def main():
    """Main entry point for T006."""
    log_info("Starting data validation (T006)...")
    
    # Determine base directory
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / 'data'
    output_path = base_dir / 'data' / 'validation_report.json'
    
    # Load dataset
    df = load_dataset(data_dir)
    
    if df is None:
        # Dataset not found - create failure report
        report = {
            "status": "FAIL",
            "reason": "Dataset not found",
            "missing_fields": [],
            "checked_fields": REQUIRED_FIELDS,
            "timestamp": None
        }
        write_report(report, output_path)
        log_error("Could not find downloaded dataset. Expected one of the predefined paths.")
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

if __name__ == '__main__':
    main()