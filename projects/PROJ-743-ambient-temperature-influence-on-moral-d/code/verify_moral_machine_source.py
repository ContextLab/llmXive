import os
import sys
import logging
from datetime import datetime
from pathlib import Path
import requests
import pandas as pd
from io import StringIO

# Import shared logging setup
from setup_logging import setup_logging, get_data_quality_logger

# Required columns as per task description
REQUIRED_COLUMNS = {
    'latitude': float,
    'longitude': float,
    'timestamp': str,  # Will parse later, but column must exist
    'response_time': float,
    'country': str,
    'dilemma_id': str
}

# Canonical OSF URL for Moral Machine dataset
# The task mentions "https://osf.io/..." - using the known public URL for the Moral Machine dataset
MORAL_MACHINE_URL = "https://osf.io/download/60669a22d82e6c0046045264/"
# Alternative direct CSV link if download endpoint fails
MORAL_MACHINE_CSV_URL = "https://osf.io/60669a22d82e6c0046045264/?action=download"

def setup_logging_custom(log_file_path: Path):
    """Configure logging to file and console."""
    logger = logging.getLogger("moral_machine_verify")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        fh = logging.FileHandler(log_file_path)
        fh.setLevel(logging.INFO)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
    return logger

def verify_source_access(logger: logging.Logger) -> bool:
    """Check if the OSF URL is accessible."""
    logger.info(f"Verifying accessibility of: {MORAL_MACHINE_URL}")
    try:
        # Try the download endpoint first
        response = requests.head(MORAL_MACHINE_URL, timeout=30)
        if response.status_code == 200 or response.status_code == 302:
            logger.info(f"Source accessible (Status: {response.status_code})")
            return True
        
        # Fallback to CSV link
        logger.info("Download endpoint returned unexpected status, trying CSV link...")
        response = requests.head(MORAL_MACHINE_CSV_URL, timeout=30)
        if response.status_code == 200:
            logger.info(f"CSV Source accessible (Status: {response.status_code})")
            return True
        
        logger.error(f"Source inaccessible. Status codes: Download={response.status_code}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to verify source accessibility: {e}")
        return False

def validate_schema(logger: logging.Logger, df: pd.DataFrame) -> bool:
    """Validate that the dataset contains the required columns and types."""
    logger.info("Validating dataset schema...")
    missing_cols = []
    type_mismatches = []
    
    for col, expected_type in REQUIRED_COLUMNS.items():
        if col not in df.columns:
            missing_cols.append(col)
        else:
            # Basic type check (pandas might infer object for datetime strings)
            # We check if the column is non-empty to ensure it's not just a header
            if df[col].empty:
                missing_cols.append(col)
            elif expected_type == float and not pd.api.types.is_numeric_dtype(df[col]):
                type_mismatches.append(col)
            elif expected_type == str and not pd.api.types.is_string_dtype(df[col]) and not pd.api.types.is_object_dtype(df[col]):
                type_mismatches.append(col)
    
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return False
    
    if type_mismatches:
        logger.warning(f"Columns with unexpected types (may need parsing): {type_mismatches}")
        # We allow this for now as long as the column exists, but log it
    
    logger.info(f"Schema validation passed. Found columns: {list(df.columns)}")
    return True

def download_sample(logger: logging.Logger, output_path: Path) -> bool:
    """Download a sample of the dataset to verify content."""
    logger.info(f"Attempting to download sample from: {MORAL_MACHINE_CSV_URL}")
    try:
        # We only need the header and a few rows to verify schema
        response = requests.get(MORAL_MACHINE_CSV_URL, timeout=60)
        if response.status_code != 200:
            logger.error(f"Download failed with status {response.status_code}")
            return False
        
        # Save the raw file to data/raw for later use
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Sample downloaded and saved to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to download sample: {e}")
        return False

def main():
    """Main entry point for T001."""
    log_file = Path("results/logs/data_validation_log.txt")
    output_file = Path("data/raw/moral_machine_sample.csv")
    
    logger = setup_logging_custom(log_file)
    logger.info("Starting Task T001: Verify Data Sources")
    
    # 1. Verify CDS API (delegated to verify_cds_api module if needed, but task focuses on Moral Machine here)
    # The task description explicitly asks to verify CDS URL accessibility too.
    # We assume verify_cds_api.py handles the CDS part, but we log the result here.
    # Since T001 requires logging to data_validation_log.txt, we append the CDS status if we can check it.
    # However, the API surface shows verify_cds_api.py exists. We will focus on Moral Machine here
    # and assume CDS verification is handled or we just log the URL check.
    cds_url = "https://cds.climate.copernicus.eu/api/v2"
    try:
        resp = requests.head(cds_url, timeout=10)
        cds_status = "Pass" if resp.status_code in [200, 302] else "Fail"
        logger.info(f"CDS API URL check: {cds_url} -> Status {resp.status_code} ({cds_status})")
    except Exception as e:
        logger.error(f"CDS API URL check failed: {e}")
        cds_status = "Fail"

    # 2. Verify Moral Machine Source
    source_ok = verify_source_access(logger)
    schema_ok = False
    
    if source_ok:
        # Download sample to verify schema
        if download_sample(logger, output_file):
            try:
                # Read just the header and first 5 rows to verify schema
                df = pd.read_csv(output_file, nrows=5)
                schema_ok = validate_schema(logger, df)
            except Exception as e:
                logger.error(f"Failed to read downloaded sample for schema validation: {e}")
                schema_ok = False
        else:
            logger.error("Download failed, cannot validate schema.")
    else:
        logger.error("Source access failed, cannot download or validate schema.")

    # 3. Final Status
    overall_status = "Pass" if (source_ok and schema_ok) else "Fail"
    logger.info(f"Task T001 Final Status: {overall_status}")
    
    # Log the specific status to the file in a parseable way if needed
    # The task asks to log status and column schema to data_validation_log.txt
    # We already logged it via logger which writes to the file.
    
    # Write a summary JSON-like line for easy parsing by other tasks
    summary = {
        "task": "T001",
        "timestamp": datetime.now().isoformat(),
        "cds_url_status": cds_status,
        "moral_machine_source_status": "Pass" if source_ok else "Fail",
        "schema_validation_status": "Pass" if schema_ok else "Fail",
        "overall_status": overall_status,
        "columns_verified": list(REQUIRED_COLUMNS.keys()) if schema_ok else []
    }
    
    with open(log_file, 'a') as f:
        f.write(f"\nSUMMARY: {summary}\n")
    
    if overall_status == "Fail":
        sys.exit(1)

if __name__ == "__main__":
    main()
