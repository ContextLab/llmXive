import os
import sys
import logging
import time
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np

# Configure logger
logger = logging.getLogger(__name__)

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_oqmd_dataset(output_path: str, max_retries: int = 3) -> str:
    """
    Fetch the OQMD Formation Energy dataset via HuggingFace.
    Implements retry logic with exponential backoff.
    Materializes the stream into a parquet file.
    """
    from datasets import load_dataset

    local_path = Path(output_path)
    local_path.parent.mkdir(parents=True, exist_ok=True)

    attempt = 0
    while attempt < max_retries:
        try:
            logger.info(f"Downloading OQMD dataset (attempt {attempt + 1}/{max_retries})...")
            dataset = load_dataset("oqmd/formation-energy", streaming=False)
            
            # Materialize to parquet
            logger.info("Materializing dataset to parquet...")
            dataset.to_parquet(str(local_path))
            
            # Calculate checksum
            checksum = calculate_sha256(str(local_path))
            checksum_file = Path("data/checksums.json")
            
            # Load existing checksums or create new
            if checksum_file.exists():
                with open(checksum_file, 'r') as f:
                    checksums = json.load(f)
            else:
                checksums = {}
            
            # Update checksums
            checksums["oqmd.parquet"] = {
                "sha256": checksum,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with open(checksum_file, 'w') as f:
                json.dump(checksums, f, indent=2)
            
            logger.info(f"Dataset saved to {local_path} with checksum {checksum}")
            return str(local_path)
            
        except Exception as e:
            attempt += 1
            if attempt < max_retries:
                wait_time = 2 ** attempt
                logger.warning(f"Download failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"Download failed after {max_retries} attempts: {e}")
                raise

def validate_structural_descriptors(df: pd.DataFrame) -> Tuple[bool, Optional[str]]:
    """
    Check if structural descriptors (radius, packing_fraction) exist.
    Returns (is_valid, error_message).
    """
    required_cols = ['radius', 'packing_fraction']
    missing = [col for col in required_cols if col not in df.columns]
    
    if missing:
        error_msg = f"OQMD schema does not support FR-001 requirements. Missing columns: {missing}"
        logger.error(error_msg)
        return False, error_msg
    
    # Check for missing values in structural descriptors
    for col in required_cols:
        if df[col].isna().any():
            logger.warning(f"Column '{col}' contains {df[col].isna().sum()} missing values")
    
    return True, None

def extract_structural_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract radius and packing_fraction from the dataset.
    Assumes these columns already exist (validated by validate_structural_descriptors).
    """
    is_valid, error_msg = validate_structural_descriptors(df)
    if not is_valid:
        raise FileNotFoundError(error_msg)
    
    # Ensure columns are present and numeric
    df['radius'] = pd.to_numeric(df['radius'], errors='coerce')
    df['packing_fraction'] = pd.to_numeric(df['packing_fraction'], errors='coerce')
    
    # Validate at least one descriptor is present for every row
    valid_rows = df[['radius', 'packing_fraction']].notna().any(axis=1)
    if not valid_rows.all():
        invalid_count = (~valid_rows).sum()
        logger.warning(f"{invalid_count} rows missing structural descriptors")
        # We proceed but log the issue; the task requires assertion
        assert invalid_count == 0, f"{invalid_count} rows missing structural descriptors"
    
    logger.info("Structural features extracted successfully")
    return df

def update_validation_report(df: pd.DataFrame, report_path: str = "data/validation_report.json") -> None:
    """
    Update validation_report.json with counts of rows where structural descriptors were extracted.
    Dependency: T005c (extract_structural_features must have run).
    """
    # Ensure report directory exists
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing report or create new
    if os.path.exists(report_path):
        with open(report_path, 'r') as f:
            report = json.load(f)
    else:
        report = {}
    
    # Extract counts
    total_rows = len(df)
    rows_with_radius = df['radius'].notna().sum()
    rows_with_packing_fraction = df['packing_fraction'].notna().sum()
    rows_with_both = df[['radius', 'packing_fraction']].notna().all(axis=1).sum()
    
    # Update report
    report['structural_descriptors'] = {
        'total_rows': int(total_rows),
        'rows_with_radius': int(rows_with_radius),
        'rows_with_packing_fraction': int(rows_with_packing_fraction),
        'rows_with_both': int(rows_with_both),
        'extraction_timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Write report
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report updated at {report_path}")
    logger.info(f"  Total rows: {total_rows}")
    logger.info(f"  Rows with radius: {rows_with_radius}")
    logger.info(f"  Rows with packing_fraction: {rows_with_packing_fraction}")
    logger.info(f"  Rows with both: {rows_with_both}")

def main():
    """Main entry point for data download and validation."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    output_path = "data/raw/oqmd.parquet"
    
    try:
        # Download dataset
        logger.info("Starting OQMD dataset download...")
        dataset_path = download_oqmd_dataset(output_path)
        
        # Load dataset
        logger.info("Loading dataset for validation...")
        df = pd.read_parquet(dataset_path)
        
        # Validate structural descriptors
        is_valid, error_msg = validate_structural_descriptors(df)
        if not is_valid:
            raise FileNotFoundError(error_msg)
        
        # Extract structural features
        logger.info("Extracting structural features...")
        df = extract_structural_features(df)
        
        # Update validation report
        logger.info("Updating validation report...")
        update_validation_report(df)
        
        logger.info("Pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()