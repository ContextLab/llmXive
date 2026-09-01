import os
import sys
import json
import csv
import logging
from pathlib import Path
from urllib.parse import urlparse

# Configure logging for the module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the required columns based on the task specification
REQUIRED_COLUMNS = {'year', 'effect_size', 'sample_size', 'field'}

class DataFetchError(Exception):
    """Custom exception for data fetching or validation errors."""
    pass

def check_url_reachability(url: str) -> bool:
    """
    Checks if a URL is reachable.
    
    Args:
        url (str): The URL to check.
        
    Returns:
        bool: True if reachable, False otherwise.
    """
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            logger.error(f"Invalid URL format: {url}")
            return False
        
        # Simple head request to check reachability without downloading full content
        # Note: This might not work for all servers that block HEAD requests
        # In such cases, we might need to rely on file existence checks or other methods
        import urllib.request
        req = urllib.request.Request(url, method='HEAD')
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status == 200
    except Exception as e:
        logger.warning(f"URL reachability check failed (might be HEAD-blocked): {e}")
        # If HEAD fails, we might still consider it potentially reachable if we can't confirm otherwise
        # But for strict validation, we return False if we can't confirm
        return False

def load_file_content(file_path: str) -> list:
    """
    Loads the content of a CSV file.
    
    Args:
        file_path (str): Path to the CSV file.
        
    Returns:
        list: List of dictionaries representing rows, or empty list if file not found.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file {file_path} not found")
    
    rows = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
        logger.info(f"Loaded {len(rows)} rows from {file_path}")
    except Exception as e:
        logger.error(f"Error reading CSV file {file_path}: {e}")
        raise DataFetchError(f"Failed to read CSV file: {e}")
    
    return rows

def validate_schema(rows: list, required_columns: set) -> dict:
    """
    Validates that the loaded data contains the required columns.
    
    Args:
        rows (list): List of dictionaries representing rows.
        required_columns (set): Set of required column names.
        
    Returns:
        dict: Validation report containing status and details.
    """
    if not rows:
        return {
            "status": "failed",
            "reason": "No data rows found in file",
            "missing_columns": list(required_columns),
            "found_columns": []
        }
    
    # Get columns from the first row (assuming consistent structure)
    found_columns = set(rows[0].keys())
    
    missing_columns = required_columns - found_columns
    extra_columns = found_columns - required_columns
    
    status = "valid" if not missing_columns else "invalid"
    
    report = {
        "status": status,
        "required_columns": sorted(list(required_columns)),
        "found_columns": sorted(list(found_columns)),
        "missing_columns": sorted(list(missing_columns)),
        "extra_columns": sorted(list(extra_columns)),
        "row_count": len(rows),
        "sample_row": rows[0] if rows else {}
    }
    
    if status == "valid":
        logger.info("Schema validation PASSED: All required columns present.")
    else:
        logger.error(f"Schema validation FAILED: Missing columns {missing_columns}")
        
    return report

def save_validation_report(report: dict, output_path: str) -> None:
    """
    Saves the validation report to a JSON file.
    
    Args:
        report (dict): The validation report to save.
        output_path (str): Path to the output JSON file.
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        logger.info(f"Validation report saved to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save validation report: {e}")
        raise DataFetchError(f"Failed to write validation report: {e}")

def validate_source(input_path: str = "data/raw/data.csv", output_path: str = "data/derived/schema_validation.json") -> dict:
    """
    Main function to validate the source data file.
    
    Args:
        input_path (str): Path to the input CSV file.
        output_path (str): Path to save the validation report.
        
    Returns:
        dict: The validation report.
    """
    logger.info(f"Starting source validation for {input_path}")
    
    # Check if file exists first
    if not os.path.exists(input_path):
        error_msg = f"Input file {input_path} not found. Please run code/download_data.py first."
        logger.error(error_msg)
        report = {
            "status": "failed",
            "reason": "File not found",
            "file_path": input_path,
            "required_columns": sorted(list(REQUIRED_COLUMNS)),
            "found_columns": [],
            "missing_columns": sorted(list(REQUIRED_COLUMNS)),
            "row_count": 0,
            "sample_row": {}
        }
        save_validation_report(report, output_path)
        raise DataFetchError(error_msg)
    
    # Load the file content
    rows = load_file_content(input_path)
    
    # Validate schema
    report = validate_schema(rows, REQUIRED_COLUMNS)
    
    # Save the report
    save_validation_report(report, output_path)
    
    # Raise an error if validation failed to stop downstream processes
    if report["status"] != "valid":
        raise DataFetchError(f"Schema validation failed: {report['reason']}")
        
    return report

def main():
    """Main entry point for the script."""
    input_path = "data/raw/data.csv"
    output_path = "data/derived/schema_validation.json"
    
    try:
        validate_source(input_path, output_path)
        logger.info("Source validation completed successfully.")
    except DataFetchError as e:
        logger.error(f"Validation process failed: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error(f"File not found error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
