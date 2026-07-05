"""
Utility functions for verifying data integrity and schema completeness.
Used by T015 to validate output of 01_data_ingestion.py
"""
import pandas as pd
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

def verify_row_count(df: pd.DataFrame, min_expected: int = 1000) -> bool:
    """
    Verify that the DataFrame has at least min_expected rows.
    """
    count = len(df)
    logger.info(f"Verifying row count: {count} (min: {min_expected})")
    if count < min_expected:
        logger.warning(f"Row count {count} is below minimum {min_expected}")
        return False
    return True

def verify_schema_completeness(df: pd.DataFrame, required_columns: List[str]) -> Dict[str, Any]:
    """
    Verify that all required columns exist in the DataFrame.
    Returns a dict with status and details.
    """
    missing = [col for col in required_columns if col not in df.columns]
    present = [col for col in required_columns if col in df.columns]
    
    result = {
        "status": "complete" if not missing else "incomplete",
        "missing_columns": missing,
        "present_columns": present,
        "total_required": len(required_columns),
        "total_present": len(present)
    }
    
    if missing:
        logger.error(f"Schema incomplete. Missing: {missing}")
    else:
        logger.info("Schema verification passed.")
        
    return result

def verify_no_empty_file(path: str) -> bool:
    """
    Verify that a file exists and is not empty.
    """
    import os
    if not os.path.exists(path):
        logger.error(f"File does not exist: {path}")
        return False
    
    if os.path.getsize(path) == 0:
        logger.error(f"File is empty: {path}")
        return False
        
    logger.info(f"File verified: {path}")
    return True