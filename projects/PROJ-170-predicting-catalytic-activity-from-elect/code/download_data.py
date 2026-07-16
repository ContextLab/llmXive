import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from config import get_project_root, get_data_path
from utils.hashing import compute_file_hash, save_hash

logger = logging.getLogger(__name__)

def handle_excluded_datasets() -> None:
    """
    Log exclusion of Materials Project and 2025 CO2 study datasets.
    Per T012, these are excluded due to verification failure/unavailability.
    """
    exclusion_log_path = get_project_root() / "outputs" / "exclusion_log.json"
    exclusion_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    exclusions = {
        "excluded_datasets": [
            {
                "name": "Materials Project",
                "reason": "Data unavailability / Verification failure"
            },
            {
                "name": "2025 CO2 study",
                "reason": "Data unavailability / Verification failure"
            }
        ],
        "pipeline_status": "Proceeding with OC20 only"
    }
    
    with open(exclusion_log_path, "w") as f:
        json.dump(exclusions, f, indent=2)
    logger.info(f"Exclusion log written to {exclusion_log_path}")

def verify_checksum(file_path: str, expected_hash: str) -> bool:
    """Verify the SHA256 checksum of a file."""
    computed = compute_file_hash(file_path)
    if computed == expected_hash:
        logger.info(f"Checksum verified for {file_path}")
        return True
    else:
        logger.error(f"Checksum mismatch for {file_path}. Expected: {expected_hash}, Got: {computed}")
        return False

def save_checksum(file_path: str, checksum_file: str) -> None:
    """Save the checksum of a file to a checksum file."""
    checksum = compute_file_hash(file_path)
    with open(checksum_file, "w") as f:
        f.write(checksum)
    logger.info(f"Checksum saved to {checksum_file}")

def download_stratified_sample() -> None:
    """
    Download a stratified sample of the OC20 dataset from HuggingFace.
    Repo: 'oc/oc20-sample-v1'
    Stratify by: 'composition_family'
    Output: 'data/raw/oc20_sample.h5'
    
    This function:
    1. Loads the 'oc/oc20-sample-v1' dataset using the HuggingFace datasets library.
    2. Performs stratified sampling based on 'composition_family'.
    3. Saves the resulting sample as an HDF5 file.
    """
    output_path = get_data_path("raw/oc20_sample.h5")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Attempting to download OC20 stratified sample to {output_path}")
    
    try:
        from datasets import load_dataset
        import pandas as pd
    except ImportError as e:
        logger.error(f"Required libraries not installed. Please install datasets and pandas: {e}")
        raise

    # Load the dataset
    # Note: We assume the dataset exists and is accessible. If not, this will raise an error.
    logger.info("Loading dataset 'oc/oc20-sample-v1' from HuggingFace...")
    dataset = load_dataset("oc/oc20-sample-v1", split="train")
    
    # Check if the stratification column exists
    if 'composition_family' not in dataset.column_names:
        raise ValueError(f"Column 'composition_family' not found in dataset. Available columns: {dataset.column_names}")
    
    logger.info(f"Dataset loaded with {len(dataset)} entries. Stratifying by 'composition_family'...")
    
    # Convert to pandas for easier stratified sampling
    df = dataset.to_pandas()
    
    # Perform stratified sampling
    # We'll take a 10% sample, stratified by composition_family
    sample_fraction = 0.1
    sampled_df = df.groupby('composition_family', group_keys=False).apply(
        lambda x: x.sample(frac=sample_fraction, replace=False)
    )
    
    logger.info(f"Stratified sample created with {len(sampled_df)} entries.")
    
    # Save to HDF5
    logger.info(f"Saving sample to {output_path}...")
    sampled_df.to_hdf(output_path, key='df', mode='w')
    
    logger.info(f"Successfully saved stratified sample to {output_path}")
    
    # Compute and save checksum
    checksum_path = output_path.with_suffix('.sha256')
    save_checksum(str(output_path), str(checksum_path))
    logger.info(f"Checksum saved to {checksum_path}")

def main() -> None:
    """Entry point for data download."""
    logging.basicConfig(level=logging.INFO)
    handle_excluded_datasets()
    download_stratified_sample()

if __name__ == "__main__":
    main()