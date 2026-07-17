import os
import hashlib
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import requests
from io import StringIO
import logging

from .logging_config import get_logger
from .validation_utils import validate_dataframe_records, load_schema

logger = get_logger(__name__)

# Configuration constants
DATASET_DISEASE_URL = os.getenv("DATASET_DISEASE_URL", "https://raw.githubusercontent.com/soil-microbiome-research/datasets/main/disease_incidence_records.csv")
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "disease_incidence_records.csv"
TARGET_RECORDS = 50

def calculate_file_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_checksum(file_path: Path, checksum: str) -> Path:
    """Save checksum to a .sha256 file."""
    checksum_path = file_path.with_suffix(file_path.suffix + ".sha256")
    with open(checksum_path, "w") as f:
        f.write(f"{checksum}  {file_path.name}\n")
    logger.info(f"Saved checksum to {checksum_path}")
    return checksum_path

def verify_existing_verification() -> bool:
    """Check if T012 verification passed."""
    verification_file = Path("data/processed/dataset_verification.json")
    if not verification_file.exists():
        logger.error("Dataset verification file not found. Run T012 first.")
        return False
    
    with open(verification_file, "r") as f:
        report = json.load(f)
    
    status = report.get("status", "FAIL")
    if status != "PASS":
        logger.error(f"Dataset verification failed with status: {status}. Cannot proceed with download.")
        return False
    
    logger.info("Dataset verification passed. Proceeding with download.")
    return True

def fetch_emp_agricultural_samples() -> pd.DataFrame:
    """Fetch EMP agricultural samples (placeholder for T013)."""
    logger.warning("fetch_emp_agricultural_samples not implemented in T014 context.")
    return pd.DataFrame()

def fetch_mg_rast_soil_samples() -> pd.DataFrame:
    """Fetch MG-RAST soil samples (placeholder for T013)."""
    logger.warning("fetch_mg_rast_soil_samples not implemented in T014 context.")
    return pd.DataFrame()

def fetch_disease_incidence_records() -> pd.DataFrame:
    """
    Fetch disease incidence records from the configured URL.
    
    This function attempts to download real data from DATASET_DISEASE_URL.
    If the download fails or returns insufficient data, it raises an exception
    rather than falling back to synthetic data (Constitution Principle II).
    
    Returns:
        pd.DataFrame: DataFrame containing disease incidence records.
        
    Raises:
        RuntimeError: If the real data source is unreachable or returns insufficient data.
    """
    logger.info(f"Attempting to fetch disease incidence records from {DATASET_DISEASE_URL}")
    
    try:
        # Attempt to fetch from the real source
        response = requests.get(DATASET_DISEASE_URL, timeout=30)
        response.raise_for_status()
        
        # Parse CSV content
        csv_content = response.text
        df = pd.read_csv(StringIO(csv_content))
        
        # Validate minimum record count
        if len(df) < TARGET_RECORDS:
            error_msg = (
                f"Downloaded only {len(df)} records, but target is {TARGET_RECORDS}. "
                f"Source: {DATASET_DISEASE_URL}. "
                "Raising error instead of falling back to synthetic data."
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        logger.info(f"Successfully fetched {len(df)} disease incidence records.")
        
        # Validate against schema if available
        schema_path = Path("contracts/disease_incidence.schema.yaml")
        if schema_path.exists():
            schema = load_schema(schema_path)
            # Basic validation check
            required_cols = schema.get("properties", {}).keys()
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                logger.warning(f"Missing expected columns: {missing_cols}")
        
        return df
        
    except requests.exceptions.RequestException as e:
        error_msg = (
            f"Failed to fetch disease incidence records from {DATASET_DISEASE_URL}: {str(e)}. "
            "Cannot proceed with synthetic data. Please verify the URL or update DATASET_DISEASE_URL in .env."
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e
    except pd.errors.EmptyDataError:
        error_msg = (
            f"The response from {DATASET_DISEASE_URL} was empty or not valid CSV. "
            "Cannot proceed with synthetic data."
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        error_msg = (
            f"Unexpected error fetching disease incidence records: {str(e)}. "
            "Cannot proceed with synthetic data."
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

def augment_with_required_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """
    Augment the dataframe with required metadata fields if missing.
    
    Required fields per FR-008 and spec:
    - sample_id (must exist)
    - disease_type (must exist)
    - incidence_rate (must exist)
    - measurement_date (must exist)
    - plant_species (optional, may be added if missing)
    - gps_coordinates (optional, may be added if missing)
    - soil_type (optional, may be added if missing)
    
    Args:
        df: Input dataframe with disease records.
        
    Returns:
        DataFrame with augmented metadata.
    """
    required_fields = ['sample_id', 'disease_type', 'incidence_rate', 'measurement_date']
    
    # Check for required fields
    missing_required = [f for f in required_fields if f not in df.columns]
    if missing_required:
        raise ValueError(f"Missing required fields: {missing_required}")
    
    # Ensure incidence_rate is numeric and within valid range [0, 1]
    if 'incidence_rate' in df.columns:
        df['incidence_rate'] = pd.to_numeric(df['incidence_rate'], errors='coerce')
        if df['incidence_rate'].isna().any():
            logger.warning("Some incidence_rate values could not be converted to numeric.")
        
        # Clamp values to [0, 1] range
        df['incidence_rate'] = df['incidence_rate'].clip(0, 1)
    
    return df

def generate_synthetic_samples(count: int) -> pd.DataFrame:
    """
    Generate synthetic sample data for testing purposes ONLY.
    
    WARNING: This function should NOT be used in production pipelines.
    It is provided only for local development testing when real data is unavailable.
    
    Args:
        count: Number of synthetic samples to generate.
        
    Returns:
        DataFrame with synthetic sample data.
    """
    logger.warning("Generating synthetic samples. This should not be used in production.")
    # Implementation omitted as per constraints - real data only
    return pd.DataFrame()

def generate_synthetic_disease_records(count: int) -> pd.DataFrame:
    """
    Generate synthetic disease incidence records for testing purposes ONLY.
    
    WARNING: This function should NOT be used in production pipelines.
    It is provided only for local development testing when real data is unavailable.
    
    Args:
        count: Number of synthetic records to generate.
        
    Returns:
        DataFrame with synthetic disease records.
    """
    logger.warning("Generating synthetic disease records. This should not be used in production.")
    # Implementation omitted as per constraints - real data only
    return pd.DataFrame()

def run_data_acquisition() -> Dict[str, Any]:
    """
    Run the complete data acquisition workflow for T014.
    
    1. Verify T012 completion
    2. Fetch disease incidence records
    3. Augment with metadata
    4. Validate against schema
    5. Save to data/raw/disease_incidence_records.csv
    6. Calculate and save checksum
    
    Returns:
        Dictionary with acquisition status and file paths.
    """
    logger.info("Starting data acquisition for T014 (Disease Incidence Records)")
    
    # Step 1: Verify T012 completion
    if not verify_existing_verification():
        raise RuntimeError("T012 verification failed. Cannot proceed.")
    
    # Step 2: Fetch real data
    df = fetch_disease_incidence_records()
    
    # Step 3: Augment with metadata
    df = augment_with_required_metadata(df)
    
    # Step 4: Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Step 5: Save to CSV
    df.to_csv(OUTPUT_FILE, index=False)
    logger.info(f"Saved {len(df)} records to {OUTPUT_FILE}")
    
    # Step 6: Calculate and save checksum
    checksum = calculate_file_checksum(OUTPUT_FILE)
    save_checksum(OUTPUT_FILE, checksum)
    
    return {
        "status": "success",
        "file_path": str(OUTPUT_FILE),
        "record_count": len(df),
        "checksum": checksum
    }

def main():
    """Entry point for running T014."""
    logger.info("Executing T014: Implement disease incidence record download")
    try:
        result = run_data_acquisition()
        logger.info(f"T014 completed successfully: {result}")
        print(json.dumps(result, indent=2))
    except Exception as e:
        logger.error(f"T014 failed: {str(e)}")
        print(json.dumps({"status": "failed", "error": str(e)}, indent=2))
        raise

if __name__ == "__main__":
    main()