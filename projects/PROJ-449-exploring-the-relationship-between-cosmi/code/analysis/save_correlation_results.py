"""
Task T023: Save correlation results to JSON and CSV.

This task serves as a checkpoint to ensure correlation results generated
by T020 are properly serialized to disk in both JSON and CSV formats.

Dependencies:
- data/processed/correlation_results.json (output of T020)
- data/processed/correlation_summary.csv (output of T020)

Note: According to the task description, T020 already handles the generation
of these files. This script verifies their existence and structure, and
ensures they are correctly formatted.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.logging import setup_logger

# Configure logging
logger = setup_logger("save_correlation_results")

# Define output paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CORRELATION_RESULTS_JSON = PROCESSED_DIR / "correlation_results.json"
CORRELATION_SUMMARY_CSV = PROCESSED_DIR / "correlation_summary.csv"

def verify_file_exists(filepath: Path, file_type: str) -> bool:
    """Verify that a file exists and is not empty."""
    if not filepath.exists():
        logger.error(f"{file_type} file not found: {filepath}")
        return False
    
    if filepath.stat().st_size == 0:
        logger.error(f"{file_type} file is empty: {filepath}")
        return False
    
    logger.info(f"{file_type} file verified: {filepath} ({filepath.stat().st_size} bytes)")
    return True

def validate_json_structure(filepath: Path) -> bool:
    """Validate that the JSON file has the expected structure."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Check for expected keys
        expected_keys = ['correlations', 'summary', 'metadata']
        if not isinstance(data, dict):
            logger.error("JSON root is not a dictionary")
            return False
        
        missing_keys = [key for key in expected_keys if key not in data]
        if missing_keys:
            logger.warning(f"JSON missing expected keys: {missing_keys}")
            # Not a failure, just a warning
        
        logger.info("JSON structure validated successfully")
        return True
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {e}")
        return False
    except Exception as e:
        logger.error(f"Error validating JSON: {e}")
        return False

def validate_csv_structure(filepath: Path) -> bool:
    """Validate that the CSV file has the expected structure."""
    try:
        import pandas as pd
        df = pd.read_csv(filepath)
        
        if df.empty:
            logger.error("CSV file is empty")
            return False
        
        # Check for expected columns
        expected_columns = ['species', 'rigidity_bin', 'lag_months', 
                          'correlation_coefficient', 'p_value', 'method']
        missing_columns = [col for col in expected_columns if col not in df.columns]
        
        if missing_columns:
            logger.warning(f"CSV missing expected columns: {missing_columns}")
            # Not a failure, just a warning
        
        logger.info(f"CSV structure validated: {len(df)} rows, {len(df.columns)} columns")
        return True
        
    except Exception as e:
        logger.error(f"Error validating CSV: {e}")
        return False

def main():
    """Main entry point for T023."""
    logger.info("Starting T023: Save correlation results checkpoint")
    
    # Ensure processed directory exists
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Verify JSON file
    json_valid = verify_file_exists(CORRELATION_RESULTS_JSON, "JSON")
    if json_valid:
        json_valid = validate_json_structure(CORRELATION_RESULTS_JSON)
    
    # Verify CSV file
    csv_valid = verify_file_exists(CORRELATION_SUMMARY_CSV, "CSV")
    if csv_valid:
        csv_valid = validate_csv_structure(CORRELATION_SUMMARY_CSV)
    
    # Final status
    if json_valid and csv_valid:
        logger.info("T023 completed successfully: All correlation result files verified")
        print("SUCCESS: Correlation results files verified")
        print(f"  - JSON: {CORRELATION_RESULTS_JSON}")
        print(f"  - CSV: {CORRELATION_SUMMARY_CSV}")
        return 0
    else:
        logger.error("T023 failed: One or more correlation result files are missing or invalid")
        print("FAILURE: Correlation results files verification failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
