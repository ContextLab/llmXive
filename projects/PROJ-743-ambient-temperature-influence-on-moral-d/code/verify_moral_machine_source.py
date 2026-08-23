"""
Verify the canonical URL for the Moral Machine dataset against the "Verified Accuracy" principle.
Confirms the dataset exists, is accessible, and contains the required columns.
"""
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
import requests
import pandas as pd

from setup_logging import setup_logging, get_data_quality_logger
from config import get_path_env_override

# Canonical URL for the Moral Machine dataset (Zenodo)
# This is the standard public URL for the "Moral Machine" dataset used in research.
MORAL_MACHINE_URL = "https://zenodo.org/record/3263626/files/moral_machine.csv.gz"

# Required columns as per FR-014 and US-1
REQUIRED_COLUMNS = {
    'latitude': 'float',
    'longitude': 'float',
    'timestamp': 'datetime',
    'response_time': 'float',
    'country': 'string',
    'dilemma_id': 'string'
}

def setup_logging_custom():
    """Setup logging for this specific script if not already done."""
    return setup_logging()

def verify_source_access(url: str, timeout: int = 30) -> tuple[bool, str]:
    """
    Verify that the URL is accessible (HTTP 200) and points to a CSV/CSV.GZ file.
    Returns (is_accessible, message).
    """
    try:
        # We only check the HEAD first to avoid downloading the whole file if possible,
        # but some servers might not support HEAD properly for this resource.
        # We'll do a GET with stream=True and check the first few bytes or just the status.
        # To be safe and strictly follow "verify accessibility", we check status code.
        # We do NOT download the full file here to save bandwidth/time, just the header.
        
        # Note: Zenodo redirects, so we need allow_redirects=True (default).
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            # Check if it looks like a data file (csv, gzip, octet-stream)
            if 'text/csv' in content_type or 'gzip' in content_type or 'application/octet-stream' in content_type:
                return True, f"URL accessible (HTTP 200). Content-Type: {content_type}"
            else:
                return False, f"URL accessible but unexpected Content-Type: {content_type}"
        else:
            # Try GET if HEAD fails or returns 405 (Method Not Allowed) which is common on some repos
            if response.status_code == 405:
                response = requests.get(url, stream=True, timeout=timeout)
                if response.status_code == 200:
                    return True, f"URL accessible via GET (HTTP 200). Content-Type: {response.headers.get('Content-Type', '')}"
                else:
                    return False, f"URL accessible via HEAD failed (405), GET failed (HTTP {response.status_code})"
            else:
                return False, f"URL not accessible (HTTP {response.status_code})"
                
    except requests.exceptions.RequestException as e:
        return False, f"Network error accessing URL: {str(e)}"

def validate_schema(df: pd.DataFrame, required_cols: dict) -> tuple[bool, list[str]]:
    """
    Validate that the dataframe contains the required columns with expected dtypes.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    missing_cols = set(required_cols.keys()) - set(df.columns)
    
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
        return False, errors
    
    # Check dtypes roughly
    # Note: Pandas dtypes might not match exactly 'float' vs 'float64', so we check category
    for col, expected_type in required_cols.items():
        actual_dtype = df[col].dtype
        if expected_type == 'float':
            if not pd.api.types.is_float_dtype(actual_dtype) and not pd.api.types.is_integer_dtype(actual_dtype):
                errors.append(f"Column '{col}' has dtype {actual_dtype}, expected float-like")
        elif expected_type == 'int':
            if not pd.api.types.is_integer_dtype(actual_dtype):
                errors.append(f"Column '{col}' has dtype {actual_dtype}, expected int-like")
        elif expected_type == 'string':
            # Pandas string or object is acceptable
            if not (pd.api.types.is_string_dtype(actual_dtype) or actual_dtype == 'object'):
                errors.append(f"Column '{col}' has dtype {actual_dtype}, expected string-like")
        elif expected_type == 'datetime':
            # Check if it's datetime64 or can be parsed
            if not pd.api.types.is_datetime64_any_dtype(actual_dtype):
                # Try to infer if it's a string that looks like datetime
                if not (pd.api.types.is_string_dtype(actual_dtype) or actual_dtype == 'object'):
                    errors.append(f"Column '{col}' has dtype {actual_dtype}, expected datetime or string-repr")
    
    return len(errors) == 0, errors

def main():
    logger = get_data_quality_logger()
    if not logger:
        # Fallback to basic logging if custom logger fails
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

    log_path = Path("results/logs/data_validation_log.txt")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting Moral Machine Source Validation for {MORAL_MACHINE_URL}")
    
    # 1. Verify Accessibility
    is_accessible, access_msg = verify_source_access(MORAL_MACHINE_URL)
    logger.info(access_msg)
    
    if not is_accessible:
        logger.error(f"Validation FAILED: {access_msg}")
        with open(log_path, 'a') as f:
            f.write(f"[{datetime.now().isoformat()}] Moral Machine Source: FAIL - {access_msg}\n")
        return 1

    # 2. Load a sample to validate schema (do not load full dataset to save memory)
    # We load just the header and a few rows to check schema
    try:
        logger.info("Downloading sample to validate schema...")
        # Use pandas to read the first few rows
        # chunksize might be overkill for just a header check, but safe for large files
        # We'll read the first 100 rows
        df_sample = pd.read_csv(MORAL_MACHINE_URL, compression='gzip', nrows=100)
        
        logger.info(f"Sample loaded. Columns found: {list(df_sample.columns)}")
        
        # 3. Validate Schema
        is_valid, schema_errors = validate_schema(df_sample, REQUIRED_COLUMNS)
        
        if is_valid:
            logger.info("Schema Validation PASSED. All required columns present with correct types.")
            status = "Pass"
            detail = f"Schema OK. Columns: {list(df_sample.columns)}"
        else:
            logger.error(f"Schema Validation FAILED. Errors: {schema_errors}")
            status = "Fail"
            detail = f"Schema Error: {'; '.join(schema_errors)}"

        # Log to file
        log_entry = f"[{datetime.now().isoformat()}] Moral Machine Source: {status} - {detail}\n"
        with open(log_path, 'a') as f:
            f.write(log_entry)
        
        # Also print to stdout for immediate feedback
        print(log_entry.strip())

        if status == "Fail":
            return 1
        else:
            return 0

    except Exception as e:
        logger.error(f"Error reading or validating dataset: {str(e)}")
        with open(log_path, 'a') as f:
            f.write(f"[{datetime.now().isoformat()}] Moral Machine Source: Fail - Error reading dataset: {str(e)}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
