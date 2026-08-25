import os
import sys
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.logging import get_logger
from utils.config import get_data_path

logger = get_logger(__name__)

def verify_csv_artifact(
    relative_path: str,
    required_columns: List[str],
    min_rows: int = 1
) -> Dict[str, Any]:
    """
    Verify that a CSV artifact exists, is non-empty, and contains required columns.
    
    Args:
        relative_path: Path relative to data/ directory (e.g., 'processed/cleaned_studies.csv')
        required_columns: List of column names that must be present
        min_rows: Minimum number of data rows expected (excluding header)
        
    Returns:
        Dictionary with verification status and details
    """
    data_root = get_data_path()
    file_path = data_root / relative_path
    
    result = {
        "path": str(file_path),
        "exists": False,
        "is_valid": False,
        "row_count": 0,
        "columns": [],
        "missing_columns": [],
        "errors": []
    }
    
    if not file_path.exists():
        result["errors"].append(f"File does not exist: {file_path}")
        logger.error(f"CSV artifact missing: {file_path}")
        return result
    
    result["exists"] = True
    
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            
            if fieldnames is None:
                result["errors"].append("CSV file is empty or has no header")
                logger.error(f"CSV file empty or no header: {file_path}")
                return result
            
            result["columns"] = list(fieldnames)
            missing = [col for col in required_columns if col not in fieldnames]
            result["missing_columns"] = missing
            
            if missing:
                result["errors"].append(f"Missing required columns: {missing}")
                logger.error(f"CSV missing columns: {missing} in {file_path}")
                return result
            
            row_count = 0
            for _ in reader:
                row_count += 1
            
            result["row_count"] = row_count
            
            if row_count < min_rows:
                result["errors"].append(f"Expected at least {min_rows} rows, found {row_count}")
                logger.warning(f"CSV has fewer rows than expected: {row_count} < {min_rows}")
                return result
            
            result["is_valid"] = True
            logger.info(f"CSV verification passed: {file_path} ({row_count} rows)")
            
    except Exception as e:
        result["errors"].append(f"Error reading CSV: {str(e)}")
        logger.error(f"Error reading CSV {file_path}: {e}")
        return result
    
    return result

def verify_log_artifact(
    relative_path: str,
    min_lines: int = 1,
    expected_patterns: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Verify that a log artifact exists and meets basic criteria.
    
    Args:
        relative_path: Path relative to data/ directory (e.g., 'raw/excluded_studies.log')
        min_lines: Minimum number of lines expected
        expected_patterns: Optional list of strings that should appear in the log
        
    Returns:
        Dictionary with verification status and details
    """
    data_root = get_data_path()
    file_path = data_root / relative_path
    
    result = {
        "path": str(file_path),
        "exists": False,
        "is_valid": False,
        "line_count": 0,
        "missing_patterns": [],
        "errors": []
    }
    
    if not file_path.exists():
        result["errors"].append(f"File does not exist: {file_path}")
        logger.error(f"Log artifact missing: {file_path}")
        return result
    
    result["exists"] = True
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        result["line_count"] = len(lines)
        
        if len(lines) < min_lines:
            result["errors"].append(f"Expected at least {min_lines} lines, found {len(lines)}")
            logger.warning(f"Log has fewer lines than expected: {len(lines)} < {min_lines}")
            return result
        
        if expected_patterns:
            content = ''.join(lines)
            missing = [pattern for pattern in expected_patterns if pattern not in content]
            result["missing_patterns"] = missing
            
            if missing:
                result["errors"].append(f"Missing expected patterns: {missing}")
                logger.warning(f"Log missing patterns: {missing}")
                return result
        
        result["is_valid"] = True
        logger.info(f"Log verification passed: {file_path} ({len(lines)} lines)")
        
    except Exception as e:
        result["errors"].append(f"Error reading log: {str(e)}")
        logger.error(f"Error reading log {file_path}: {e}")
        return result
    
    return result

def main():
    """
    Main entry point for verifying T014-T018 outputs.
    Validates that cleaned_studies.csv and excluded_studies.log exist and are valid.
    """
    logger.info("Starting output verification for T014-T018")
    
    # Define expected artifacts and their requirements
    csv_artifact = {
        "path": "processed/cleaned_studies.csv",
        "columns": [
            "study_id", "title", "year", "sample_size", 
            "mean_age", "asd_diagnosis", "intervention_type",
            "delivery_format", "effect_size", "se_effect_size"
        ],
        "min_rows": 1
    }
    
    log_artifact = {
        "path": "raw/excluded_studies.log",
        "min_lines": 0,  # Can be empty if no exclusions, but file must exist
        "patterns": []   # No specific patterns required, just existence
    }
    
    all_passed = True
    
    # Verify CSV
    logger.info(f"Verifying CSV: {csv_artifact['path']}")
    csv_result = verify_csv_artifact(
        csv_artifact["path"],
        csv_artifact["columns"],
        csv_artifact["min_rows"]
    )
    
    if not csv_result["is_valid"]:
        all_passed = False
        logger.error(f"CSV verification failed: {csv_result['errors']}")
    else:
        logger.info(f"CSV passed: {csv_result['row_count']} rows, columns: {csv_result['columns']}")
    
    # Verify Log
    logger.info(f"Verifying Log: {log_artifact['path']}")
    log_result = verify_log_artifact(
        log_artifact["path"],
        log_artifact["min_lines"],
        log_artifact["patterns"]
    )
    
    if not log_result["is_valid"]:
        all_passed = False
        logger.error(f"Log verification failed: {log_result['errors']}")
    else:
        logger.info(f"Log passed: {log_result['line_count']} lines")
    
    # Summary
    if all_passed:
        logger.info("T019 VERIFICATION PASSED: All artifacts present and valid")
        print("SUCCESS: T019 verification completed. All artifacts validated.")
        sys.exit(0)
    else:
        logger.error("T019 VERIFICATION FAILED: One or more artifacts missing or invalid")
        print("FAILURE: T019 verification failed. Check logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
