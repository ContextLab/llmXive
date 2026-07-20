import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, List

# Ensure the project root is in the path for imports if run as a script
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from utils.logging import get_logger

logger = get_logger(__name__)

def check_csv_integrity(file_path: str, min_rows: int = 1, required_columns: List[str] = None) -> Dict[str, Any]:
    """
    Checks if a CSV file exists, is not empty, has the required number of rows,
    and contains the required columns.

    Args:
        file_path: Path to the CSV file.
        min_rows: Minimum number of data rows required (excluding header).
        required_columns: List of column names that must exist in the CSV.

    Returns:
        A dictionary with validation details.
    """
    result = {
        "file": file_path,
        "exists": False,
        "valid": False,
        "row_count": 0,
        "columns": [],
        "errors": []
    }

    if not os.path.exists(file_path):
        result["errors"].append(f"File not found: {file_path}")
        logger.error(f"File not found: {file_path}")
        return result

    result["exists"] = True

    try:
        import pandas as pd
        df = pd.read_csv(file_path)
        
        result["row_count"] = len(df)
        result["columns"] = list(df.columns)

        if len(df) < min_rows:
            result["errors"].append(f"Insufficient rows: found {len(df)}, expected >= {min_rows}")
            logger.error(f"Insufficient rows in {file_path}: {len(df)}")
            return result

        if required_columns:
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                result["errors"].append(f"Missing required columns: {missing_cols}")
                logger.error(f"Missing columns in {file_path}: {missing_cols}")
                return result

        result["valid"] = True
        logger.info(f"Integrity check passed for {file_path}: {len(df)} rows, columns: {list(df.columns)}")
        
    except Exception as e:
        result["errors"].append(f"Error reading file: {str(e)}")
        logger.error(f"Error reading {file_path}: {str(e)}", exc_info=True)
        return result

    return result

def main():
    """
    Main entry point for the data integrity check task (T014).
    Reads raw data files, validates them, and writes a validation_status.json.
    """
    # Define paths relative to the project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    data_raw_dir = os.path.join(project_root, "data", "raw")
    
    gdelt_path = os.path.join(data_raw_dir, "gdelt_events.csv")
    trends_path = os.path.join(data_raw_dir, "google_trends.csv")
    
    output_path = os.path.join(project_root, "validation_status.json")

    logger.info("Starting data integrity checks for T014...")

    # Define required columns based on typical fetch outputs
    # These should match what fetch_gdelt.py and fetch_google_trends.py produce
    gdelt_required = ["date", "event_count"] # Adjust if actual schema differs
    trends_required = ["date", "keyword", "value"] # Adjust if actual schema differs

    # Run checks
    gdelt_status = check_csv_integrity(gdelt_path, min_rows=1, required_columns=gdelt_required)
    trends_status = check_csv_integrity(trends_path, min_rows=1, required_columns=trends_required)

    all_valid = gdelt_status["valid"] and trends_status["valid"]

    summary = {
        "timestamp": datetime.now().isoformat(),
        "task_id": "T014",
        "overall_status": "PASSED" if all_valid else "FAILED",
        "checks": {
            "gdelt_events": gdelt_status,
            "google_trends": trends_status
        }
    }

    # Write validation status to JSON
    try:
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Validation status written to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write validation status: {e}")
        sys.exit(1)

    if not all_valid:
        logger.error("Data integrity check FAILED. One or more files are invalid.")
        sys.exit(1)
    
    logger.info("Data integrity check PASSED.")
    sys.exit(0)

if __name__ == "__main__":
    main()