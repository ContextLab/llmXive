import os
import sys
import csv
import json
import logging
from pathlib import Path

# Import config for path constants
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(config.PROJECT_ROOT, 'data', 'calibration', 'calibration.log'))
    ]
)
logger = logging.getLogger(__name__)

# Constants for required schema
REQUIRED_COLUMNS = ['snippet_id', 'model', 'prompt_id', 'human_label']

def load_csv(file_path: str) -> list:
    """Load a CSV file and return a list of dictionaries."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def load_human_labels(file_path: str) -> list:
    """Load human labels from CSV."""
    return load_csv(file_path)

def load_findings(file_path: str) -> list:
    """Load findings from CSV."""
    return load_csv(file_path)

def validate_schema(data: list, required_columns: list) -> tuple:
    """
    Validate that the CSV data contains all required columns.
    Returns (is_valid, missing_columns, extra_columns).
    """
    if not data:
        return False, [], []
    
    actual_columns = set(data[0].keys())
    required_set = set(required_columns)
    
    missing = list(required_set - actual_columns)
    extra = list(actual_set - required_set) if (actual_set := actual_columns) else []
    
    return len(missing) == 0, missing, extra

def validate_non_empty(data: list) -> bool:
    """Check if the dataset has at least one row."""
    return len(data) > 0

def validate_human_labels(labels: list) -> dict:
    """
    Validate human labels data.
    Returns a validation report dictionary.
    """
    report = {
        "file_exists": True,
        "schema_valid": False,
        "non_empty": False,
        "missing_columns": [],
        "extra_columns": [],
        "row_count": 0,
        "is_valid": False,
        "errors": []
    }

    # Check schema
    is_schema_valid, missing_cols, extra_cols = validate_schema(labels, REQUIRED_COLUMNS)
    report["schema_valid"] = is_schema_valid
    report["missing_columns"] = missing_cols
    report["extra_columns"] = extra_cols

    if not is_schema_valid:
        report["errors"].append(f"Schema validation failed. Missing columns: {missing_cols}")

    # Check non-empty
    is_non_empty = validate_non_empty(labels)
    report["non_empty"] = is_non_empty
    report["row_count"] = len(labels)

    if not is_non_empty:
        report["errors"].append("Dataset is empty. At least one row is required.")

    # Final validation status
    report["is_valid"] = is_schema_valid and is_non_empty

    if not report["is_valid"]:
        report["errors"].append("Overall validation failed.")
    else:
        report["message"] = "Validation successful."

    return report

def save_results(report: dict, output_path: str):
    """Save the validation report to a JSON file."""
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report saved to {output_path}")

def main():
    """
    Main entry point for T022d: Validate Human Labels.
    Validates data/calibration/human_labels.csv and outputs data/calibration/validation_report.json.
    """
    input_file = os.path.join(config.PROJECT_ROOT, 'data', 'calibration', 'human_labels.csv')
    output_file = os.path.join(config.PROJECT_ROOT, 'data', 'calibration', 'validation_report.json')

    logger.info(f"Starting validation for: {input_file}")

    # Check file existence first
    if not os.path.exists(input_file):
        error_report = {
            "file_exists": False,
            "schema_valid": False,
            "non_empty": False,
            "missing_columns": [],
            "extra_columns": [],
            "row_count": 0,
            "is_valid": False,
            "errors": [f"Required file not found: {input_file}"]
        }
        save_results(error_report, output_file)
        logger.error("Validation failed: File not found.")
        sys.exit(1)

    try:
        # Load data
        labels = load_human_labels(input_file)
        
        # Validate
        report = validate_human_labels(labels)
        
        # Save report
        save_results(report, output_file)
        
        if report["is_valid"]:
            logger.info("Validation passed.")
            sys.exit(0)
        else:
            logger.error(f"Validation failed: {report['errors']}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Unexpected error during validation: {str(e)}")
        error_report = {
            "file_exists": True,
            "schema_valid": False,
            "non_empty": False,
            "missing_columns": [],
            "extra_columns": [],
            "row_count": 0,
            "is_valid": False,
            "errors": [f"Unexpected error: {str(e)}"]
        }
        save_results(error_report, output_file)
        sys.exit(1)

if __name__ == "__main__":
    main()