"""
Validate raw OpenNeuro EEG data for required demographic fields: Age, Sex, BMI.
Diet is optional/absent in OpenNeuro and will not be checked.
Logs errors if required fields are missing.
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import project utilities
from config import get_project_root
from logging_config import get_logger, log_structured_event, flush_yaml_logs

REQUIRED_FIELDS = ['age', 'sex', 'bmi']
OPTIONAL_FIELDS = ['diet']  # Explicitly noted as optional/absent for OpenNeuro

def get_logger() -> logging.Logger:
    """Get the specific logger for EEG validation."""
    return logging.getLogger('validate_eeg_fields')

def load_raw_data(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load raw data from a CSV file.
    Expects a standard CSV with headers.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Raw EEG data file not found: {file_path}")
    
    # Try to load with pandas, fallback to csv if pandas not strictly available in env
    # but pandas is in requirements.txt
    try:
        import pandas as pd
        df = pd.read_csv(file_path)
        return df.to_dict('records')
    except ImportError:
        # Fallback if pandas is somehow missing (should not happen per requirements)
        import csv
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)

def validate_fields(data: List[Dict[str, Any]], required: List[str], optional: List[str]) -> Dict[str, Any]:
    """
    Validate that all required fields exist in the data records.
    Returns a summary of validation results.
    """
    errors = []
    missing_counts = {field: 0 for field in required}
    total_records = len(data)
    
    for idx, record in enumerate(data):
        # Normalize keys to lowercase to handle case variations
        record_keys = {k.lower(): k for k in record.keys()}
        
        for field in required:
            if field.lower() not in record_keys:
                errors.append(f"Row {idx}: Missing required field '{field}'")
                missing_counts[field] += 1
            else:
                # Check if value is actually present (not None/empty)
                val = record[record_keys[field.lower()]]
                if val is None or (isinstance(val, str) and val.strip() == ""):
                    errors.append(f"Row {idx}: Required field '{field}' is empty")
                    missing_counts[field] += 1
        
        # Log optional field presence (info only)
        for field in optional:
            if field.lower() in record_keys:
                # Optional field exists
                pass
            else:
                # Optional field missing is expected for OpenNeuro
                pass

    return {
        'total_records': total_records,
        'missing_counts': missing_counts,
        'errors': errors,
        'valid': len(errors) == 0
    }

def main():
    """Main entry point for EEG field validation."""
    parser = argparse.ArgumentParser(description='Validate raw OpenNeuro EEG data fields.')
    parser.add_argument('--input', '-i', type=str, required=False,
                        help='Path to raw EEG data CSV. Defaults to data/raw/openneuro_eeg/processed_eeg.csv')
    parser.add_argument('--log-file', '-l', type=str, default=None,
                        help='Path to log file. Defaults to artifacts/validation_eeg.log')
    
    args = parser.parse_args()
    
    # Setup paths
    project_root = get_project_root()
    if args.input:
        input_path = Path(args.input)
    else:
        # Default path based on project structure
        input_path = project_root / 'data' / 'raw' / 'openneuro_eeg' / 'processed_eeg.csv'
    
    # If the default raw file doesn't exist, try the processed one if it exists (common in pipeline)
    if not input_path.exists():
        alt_path = project_root / 'data' / 'processed' / 'eeg_features.csv'
        if alt_path.exists():
            logging.warning(f"Default raw path not found, trying processed path: {alt_path}")
            input_path = alt_path
        else:
            logging.error(f"Neither default raw path nor processed path found. Expected: {input_path}")
            # We cannot proceed without data, but we must not fake it.
            # Raise error to fail loudly as per constraints.
            print(f"ERROR: Input file not found: {input_path}")
            sys.exit(1)

    # Setup logging
    log_file = Path(args.log_file) if args.log_file else (project_root / 'artifacts' / 'validation_eeg.log')
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger = get_logger()
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    fh = logging.FileHandler(log_file, mode='w')
    fh.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    logger.info(f"Starting EEG field validation for file: {input_path}")
    
    try:
        # Load data
        data = load_raw_data(input_path)
        logger.info(f"Loaded {len(data)} records from {input_path}")
        
        # Validate
        results = validate_fields(data, REQUIRED_FIELDS, OPTIONAL_FIELDS)
        
        # Log results
        log_structured_event(logger, 'validation_result', results)
        
        if results['valid']:
            logger.info("Validation PASSED: All required fields present.")
            print("Validation PASSED: All required fields (Age, Sex, BMI) are present.")
            sys.exit(0)
        else:
            logger.error(f"Validation FAILED: {len(results['errors'])} errors found.")
            for err in results['errors'][:10]: # Log first 10 errors
                logger.error(err)
            if len(results['errors']) > 10:
                logger.error(f"... and {len(results['errors']) - 10} more errors.")
            print(f"Validation FAILED: {len(results['errors'])} errors found. Check logs.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Unexpected error during validation: {str(e)}")
        print(f"ERROR: {str(e)}")
        sys.exit(1)
    finally:
        flush_yaml_logs()

if __name__ == '__main__':
    main()
