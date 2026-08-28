import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from utils.logging import get_logger

logger = get_logger(__name__)

def check_csv_integrity(file_path: str, min_rows: int = 1) -> Dict[str, Any]:
    """
    Check if a CSV file exists, is non-empty, and has the required number of rows.
    
    Args:
        file_path: Path to the CSV file
        min_rows: Minimum number of data rows required (default: 1)
        
    Returns:
        Dictionary with validation results
    """
    result = {
        "file": file_path,
        "exists": False,
        "is_valid": False,
        "row_count": 0,
        "error": None
    }
    
    if not os.path.exists(file_path):
        result["error"] = f"File not found: {file_path}"
        logger.error(result["error"])
        return result
    
    result["exists"] = True
    
    try:
        import pandas as pd
        df = pd.read_csv(file_path)
        result["row_count"] = len(df)
        
        if result["row_count"] < min_rows:
            result["error"] = f"Insufficient rows: {result['row_count']} < {min_rows}"
            logger.error(result["error"])
            return result
        
        # Check for essential columns (basic validation)
        if df.empty:
            result["error"] = "DataFrame is empty"
            logger.error(result["error"])
            return result
        
        result["is_valid"] = True
        logger.info(f"File {file_path} validated successfully: {result['row_count']} rows")
        
    except Exception as e:
        result["error"] = f"Error reading file: {str(e)}"
        logger.error(result["error"])
    
    return result

def main():
    """
    Main entry point for data integrity checks.
    Verifies raw data files and writes validation status to JSON.
    """
    # Define target paths relative to project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    gdelt_path = os.path.join(project_root, "data", "raw", "gdelt_events.csv")
    trends_path = os.path.join(project_root, "data", "raw", "google_trends.csv")
    output_path = os.path.join(project_root, "data", "raw", "validation_status.json")
    
    logger.info("Starting data integrity checks...")
    
    # Check GDELT data
    logger.info(f"Checking GDELT data: {gdelt_path}")
    gdelt_status = check_csv_integrity(gdelt_path, min_rows=1)
    
    # Check Google Trends data
    logger.info(f"Checking Google Trends data: {trends_path}")
    trends_status = check_csv_integrity(trends_path, min_rows=1)
    
    # Compile overall status
    all_valid = gdelt_status["is_valid"] and trends_status["is_valid"]
    
    validation_report = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "PASSED" if all_valid else "FAILED",
        "checks": {
            "gdelt_events": gdelt_status,
            "google_trends": trends_status
        }
    }
    
    # Write validation status to JSON
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(validation_report, f, indent=2)
        logger.info(f"Validation report written to: {output_path}")
    except Exception as e:
        logger.error(f"Failed to write validation report: {e}")
        sys.exit(1)
    
    # Exit with appropriate code
    if not all_valid:
        logger.error("Data integrity check FAILED. One or more files are missing or invalid.")
        sys.exit(1)
    else:
        logger.info("Data integrity check PASSED.")
        sys.exit(0)

if __name__ == "__main__":
    main()
