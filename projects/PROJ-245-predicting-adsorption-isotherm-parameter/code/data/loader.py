"""
Hybrid Data Loader for Adsorption Isotherm Pipeline.

This module implements the logic to attempt fetching real data from external sources
(NIST/MOF-1000) and gracefully falling back to synthetic data generation if the fetch fails.
It ensures the pipeline remains runnable for CI/CD even without verified external sources.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

# Import from project modules
from data.download import (
    attempt_nist_fetch,
    attempt_fallback_fetch,
    write_verification_log,
    sanitize_filename
)
from data.synthetic_gen import generate_synthetic_data
from data.preprocess import preprocess_pipeline
from data.validate_schema import validate_dataframe, load_schema
from data.verified_source_enforcer import detect_data_source_type

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
VERIFICATION_LOG_PATH = DATA_DIR / "verification_log.json"
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"


def ensure_directories():
    """Ensure all necessary directories exist."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_raw_data(source_type: str = "auto") -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Attempt to load raw data from real sources. If that fails, generate synthetic data.
    
    Args:
        source_type: "real", "synthetic", or "auto" (default).
    
    Returns:
        Tuple of (data_dict, source_status)
        - data_dict: The loaded/generated data as a dictionary with 'df' and 'metadata'.
        - source_status: "REAL", "SYNTHETIC", or "FAILED" (if both fail).
    """
    ensure_directories()
    
    if source_type == "synthetic":
        logger.info("Forcing synthetic data generation.")
        return generate_synthetic_data(), "SYNTHETIC"
    
    # Attempt real data fetch
    logger.info("Attempting to fetch real data from NIST/MOF-1000 sources...")
    
    real_data, fetch_status = attempt_nist_fetch()
    
    if fetch_status == "SUCCESS" and real_data is not None:
        logger.info("Successfully fetched real data.")
        write_verification_log("SUCCESS", "Real data fetched successfully from NIST/MOF-1000.")
        return real_data, "REAL"
    
    # If NIST fetch failed, try fallback sources
    logger.warning("NIST fetch failed. Attempting fallback sources...")
    real_data, fallback_status = attempt_fallback_fetch()
    
    if fallback_status == "SUCCESS" and real_data is not None:
        logger.info("Successfully fetched real data from fallback source.")
        write_verification_log("SUCCESS", "Real data fetched successfully from fallback source.")
        return real_data, "REAL"
    
    # All real sources failed
    logger.error("All real data sources failed. Switching to synthetic data generation.")
    write_verification_log(
        "UNVERIFIED", 
        "Real data fetch failed from all sources. Switching to synthetic data for pipeline validation.",
        rationale="NIST/MOF-1000 data not accessible; synthetic data used for CI reproducibility."
    )
    
    synthetic_data = generate_synthetic_data()
    return synthetic_data, "SYNTHETIC"


def validate_loaded_data(data_dict: Dict[str, Any], source_status: str) -> bool:
    """
    Validate the loaded data against the schema.
    
    Args:
        data_dict: The data dictionary containing 'df' and 'metadata'.
        source_status: The source status ("REAL" or "SYNTHETIC").
    
    Returns:
        True if validation passes, False otherwise.
    """
    if "df" not in data_dict:
        logger.error("Loaded data dictionary missing 'df' key.")
        return False
    
    df = data_dict["df"]
    schema = load_schema(SCHEMA_PATH)
    
    is_valid, errors = validate_dataframe(df, schema)
    
    if not is_valid:
        logger.error(f"Data validation failed: {errors}")
        return False
    
    logger.info("Data validation passed.")
    return True


def load_and_preprocess_data(source_type: str = "auto") -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Load raw data (real or synthetic), validate it, and run the preprocessing pipeline.
    
    Args:
        source_type: "real", "synthetic", or "auto".
    
    Returns:
        Tuple of (processed_data_dict, source_status)
    """
    # Step 1: Load raw data
    raw_data_dict, source_status = load_raw_data(source_type)
    
    if raw_data_dict is None:
        logger.error("Failed to load or generate any data.")
        return None, "FAILED"
    
    # Step 2: Validate raw data
    if not validate_loaded_data(raw_data_dict, source_status):
        logger.error("Raw data validation failed. Cannot proceed.")
        return None, "FAILED"
    
    # Step 3: Run preprocessing pipeline
    logger.info("Running preprocessing pipeline...")
    processed_data_dict = preprocess_pipeline(raw_data_dict["df"])
    
    if processed_data_dict is None:
        logger.error("Preprocessing pipeline failed.")
        return None, "FAILED"
    
    # Step 4: Attach source metadata to processed data
    processed_data_dict["metadata"]["source_status"] = source_status
    processed_data_dict["metadata"]["source_type"] = source_type
    
    logger.info(f"Data loading and preprocessing complete. Source: {source_status}")
    return processed_data_dict, source_status


def main():
    """
    Main entry point for the Hybrid Data Loader.
    Runs the full load -> validate -> preprocess pipeline.
    """
    logger.info("Starting Hybrid Data Loader...")
    
    # Default to auto-detection
    processed_data, status = load_and_preprocess_data(source_type="auto")
    
    if processed_data is None:
        logger.error("Pipeline failed to produce valid data.")
        sys.exit(1)
    
    # Save processed data
    output_path = PROCESSED_DIR / "curated_dataset.csv"
    processed_data["df"].to_csv(output_path, index=False)
    logger.info(f"Processed data saved to {output_path}")
    
    # Log summary
    logger.info(f"Final dataset shape: {processed_data['df'].shape}")
    logger.info(f"Source Status: {status}")
    logger.info(f"Columns: {list(processed_data['df'].columns)}")
    
    return processed_data, status


if __name__ == "__main__":
    main()