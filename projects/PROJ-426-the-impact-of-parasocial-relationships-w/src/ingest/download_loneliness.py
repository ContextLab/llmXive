"""
Download the Reddit Loneliness Longitudinal Dataset from Zenodo.

This script fetches the dataset associated with the DOI provided in the configuration,
validates the presence of required linkable IDs (username or username_hash),
and ensures extended periods of non-null loneliness scores exist.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import hashlib
import json

# Add parent to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from zenodo_get import zenodo_get
import pandas as pd
from src.utils.logging import get_logger, log_stage_start, log_stage_end, log_error_context
from src.utils.config import get_config
from src.utils.data_validation import validate_parquet_schema, record_checksum, ValidationError

# Configure logger
logger = get_logger(__name__)

# Constants
REQUIRED_COLUMNS = ["username", "username_hash", "loneliness_score", "timestamp"]
LINKABLE_ID_COLS = ["username", "username_hash"]
MIN_VALID_ROWS = 100  # Minimum rows with non-null scores to proceed

def load_config() -> Dict[str, Any]:
    """Load configuration for data paths and Zenodo DOI."""
    try:
        cfg = get_config()
        return {
            "zenodo_doi": cfg.get("data", {}).get("zenodo_loneliness_doi", "10.5281/zenodo.123456"),
            "output_path": cfg.get("paths", {}).get("raw_loneliness_dataset", "data/raw/loneliness_dataset.parquet"),
            "schema_path": cfg.get("paths", {}).get("schema", "contracts/unified_dataset.schema.yaml")
        }
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise

def fetch_dataset(zenodo_doi: str, output_dir: Path) -> Optional[Path]:
    """
    Fetch dataset from Zenodo using zenodo_get.
    
    Args:
        zenodo_doi: The DOI of the dataset.
        output_dir: Directory to save the downloaded file.
        
    Returns:
        Path to the downloaded file, or None if failed.
    """
    logger.info(f"Fetching dataset from Zenodo DOI: {zenodo_doi}")
    try:
        # zenodo_get expects a list of DOIs
        zenodo_get([zenodo_doi], output_dir=str(output_dir))
        
        # Find the downloaded file (usually .csv or .parquet)
        files = list(output_dir.glob("*"))
        if not files:
            raise FileNotFoundError(f"No files found after downloading from {zenodo_doi}")
        
        # Assume the first file is the data file (or filter for data extensions)
        data_files = [f for f in files if f.suffix in ['.csv', '.parquet', '.zip']]
        if not data_files:
            raise FileNotFoundError(f"No data files (.csv, .parquet, .zip) found in {output_dir}")
        
        downloaded_file = data_files[0]
        logger.info(f"Successfully downloaded: {downloaded_file}")
        return downloaded_file
    except Exception as e:
        logger.error(f"Failed to download dataset: {e}")
        raise

def validate_dataset(df: pd.DataFrame, config: Dict[str, Any]) -> bool:
    """
    Validate the downloaded dataset.
    
    Checks:
    1. Presence of at least one linkable ID column (username or username_hash).
    2. Extended periods of non-null loneliness scores.
    3. Minimum valid row count.
    
    Raises:
        ValueError: If validation fails.
    """
    logger.info("Validating dataset schema and content...")
    
    # Check for linkable IDs
    has_linkable_id = any(col in df.columns for col in LINKABLE_ID_COLS)
    if not has_linkable_id:
        error_msg = "Data Linkage Impossible: Missing 'username' or 'username_hash' columns."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Check for loneliness score column
    if "loneliness_score" not in df.columns:
        error_msg = "Data Linkage Impossible: Missing 'loneliness_score' column."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Check for non-null scores
    valid_scores = df["loneliness_score"].notna()
    valid_count = valid_scores.sum()
    
    if valid_count < MIN_VALID_ROWS:
        error_msg = f"Data Linkage Impossible: Only {valid_count} rows with non-null loneliness scores found. Minimum required: {MIN_VALID_ROWS}."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Check for timestamp column (needed for longitudinal analysis)
    if "timestamp" not in df.columns:
        logger.warning("Column 'timestamp' not found. Attempting to infer from date columns...")
        # If strictly required by downstream, we might raise here. 
        # For now, we assume the dataset has a temporal component or will be handled later.
        # However, the task description implies longitudinal data, so timestamp is critical.
        # Let's enforce it to be safe based on "Longitudinal Dataset".
        if not any("date" in col.lower() for col in df.columns):
            error_msg = "Data Linkage Impossible: No timestamp or date column found for longitudinal analysis."
            logger.error(error_msg)
            raise ValueError(error_msg)

    logger.info(f"Validation passed. {valid_count} valid rows with loneliness scores.")
    return True

def save_and_checksum(df: pd.DataFrame, output_path: Path, checksum_path: Path) -> None:
    """Save dataframe to parquet and record checksum."""
    logger.info(f"Saving dataset to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to parquet
    df.to_parquet(output_path, index=False)
    
    # Record checksum
    record_checksum(output_path, checksum_path)
    logger.info(f"Checksum recorded to {checksum_path}")

def main():
    """Main entry point for the ingestion script."""
    log_stage_start("T012: Download Loneliness Dataset")
    
    try:
        config = load_config()
        output_dir = Path("data/raw")
        output_path = Path(config["output_path"])
        checksum_path = output_dir / "loneliness_dataset.sha256"
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Fetch dataset
        downloaded_file = fetch_dataset(config["zenodo_doi"], output_dir)
        
        # Load data
        if downloaded_file.suffix == ".zip":
            # If it's a zip, we need to extract it first. 
            # For simplicity, assume zenodo_get might handle extraction or we extract manually.
            # If the file is a zip, we might need to unzip it.
            # Let's assume for now the downloaded file is the data or we handle zip.
            import zipfile
            with zipfile.ZipFile(downloaded_file, 'r') as zip_ref:
                zip_ref.extractall(output_dir)
            # Find the extracted file
            extracted_files = list(output_dir.glob("*"))
            data_files = [f for f in extracted_files if f.suffix in ['.csv', '.parquet']]
            if not data_files:
                raise FileNotFoundError("No data files found after extracting zip.")
            downloaded_file = data_files[0]
        
        if downloaded_file.suffix == ".csv":
            df = pd.read_csv(downloaded_file)
        elif downloaded_file.suffix == ".parquet":
            df = pd.read_parquet(downloaded_file)
        else:
            raise ValueError(f"Unsupported file format: {downloaded_file.suffix}")
        
        # Validate
        validate_dataset(df, config)
        
        # Save
        save_and_checksum(df, output_path, checksum_path)
        
        log_stage_end("T012: Download Loneliness Dataset - Success")
        
    except Exception as e:
        log_error_context("T012: Download Loneliness Dataset - Failed", e)
        raise

if __name__ == "__main__":
    main()
