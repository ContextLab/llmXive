import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

# Import logging setup from project config
from logging_config import setup_logging, get_logger
from config import get_project_root, get_data_path, get_output_path
from utils.hashing import compute_file_hash, save_hash, verify_file_hash

# HuggingFace datasets for real OC20 access
from datasets import load_dataset
import h5py
import pandas as pd
import numpy as np

logger = get_logger(__name__)

# Constants
DATASET_ID = "oc/oc20"
DATASET_FILE = "oc20.h5"
OUTPUT_FILE = "oc20_sample.h5"
STRATIFICATION_COLUMN = "composition_family"
SAMPLE_SIZE = 5000  # Reasonable sample size for CPU-only execution
RANDOM_SEED = 42

def load_expected_checksum(checksum_file: Optional[Path] = None) -> Dict[str, str]:
    """Load expected checksums from a JSON file if it exists."""
    if checksum_file is None:
        checksum_file = get_data_path() / "expected_checksums.json"
    
    if not checksum_file.exists():
        return {}
    
    with open(checksum_file, 'r') as f:
        return json.load(f)

def save_checksum(checksum_data: Dict[str, str], checksum_file: Optional[Path] = None) -> None:
    """Save checksums to a JSON file."""
    if checksum_file is None:
        checksum_file = get_data_path() / "expected_checksums.json"
    
    with open(checksum_file, 'w') as f:
        json.dump(checksum_data, f, indent=2)

def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """Compute the hash of a file."""
    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def verify_checksum(file_path: Path, expected_hash: str, algorithm: str = "sha256") -> bool:
    """Verify a file's checksum against an expected value."""
    actual_hash = compute_file_hash(file_path, algorithm)
    return actual_hash == expected_hash

def verify_downloaded_data(file_path: Path, expected_hash: Optional[str] = None) -> bool:
    """Verify the downloaded data file."""
    if not file_path.exists():
        logger.error(f"Downloaded file not found: {file_path}")
        return False
    
    if expected_hash:
        return verify_checksum(file_path, expected_hash)
    
    # If no expected hash, just confirm file exists and is non-empty
    return file_path.stat().st_size > 0

def handle_excluded_datasets(reason: str) -> None:
    """Log exclusion of datasets as per Scope Adjustment."""
    logger.warning(f"Excluded dataset: {reason}")
    # This is handled in T012, but we log here for consistency

def download_stratified_sample(
    dataset_id: str = DATASET_ID,
    output_file: Optional[Path] = None,
    stratification_col: str = STRATIFICATION_COLUMN,
    sample_size: int = SAMPLE_SIZE,
    seed: int = RANDOM_SEED
) -> Path:
    """
    Download a stratified sample of the OC20 dataset from HuggingFace.
    
    Args:
        dataset_id: HuggingFace dataset ID
        output_file: Path to save the output file
        stratification_col: Column to use for stratification
        sample_size: Number of samples to extract
        seed: Random seed for reproducibility
    
    Returns:
        Path to the saved output file
    """
    if output_file is None:
        output_file = get_data_path() / "raw" / OUTPUT_FILE
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Loading dataset {dataset_id} from HuggingFace...")
    
    try:
        # Load the dataset with streaming to handle large size
        # OC20 is large, so we use streaming and sample on the fly
        dataset = load_dataset(dataset_id, split="train", streaming=True)
        
        logger.info(f"Dataset loaded. Stratifying by '{stratification_col}'...")
        
        # Collect samples ensuring stratification
        # We'll group by composition_family first, then sample proportionally
        samples_by_family = {}
        total_samples = 0
        
        # First pass: count samples per family
        for item in dataset:
            family = item.get(stratification_col, "unknown")
            if family not in samples_by_family:
                samples_by_family[family] = []
            samples_by_family[family].append(item)
            total_samples += 1
            # Limit to avoid memory issues during counting
            if total_samples >= 100000:  # Reasonable limit for counting
                break
        
        logger.info(f"Found {len(samples_by_family)} composition families")
        
        # Calculate proportional sample size per family
        stratified_samples = []
        samples_per_family = max(1, sample_size // len(samples_by_family))
        
        for family, items in samples_by_family.items():
            # Take samples from this family
            n_samples = min(samples_per_family, len(items))
            if n_samples > 0:
                selected = np.random.RandomState(seed).choice(
                    len(items), size=n_samples, replace=False
                )
                for idx in selected:
                    stratified_samples.append(items[idx])
        
        # Shuffle the combined samples
        np.random.RandomState(seed).shuffle(stratified_samples)
        
        logger.info(f"Created stratified sample with {len(stratified_samples)} entries")
        
        # Convert to DataFrame and save as HDF5
        df = pd.DataFrame(stratified_samples)
        
        logger.info(f"Saving stratified sample to {output_file}...")
        df.to_hdf(output_file, key='data', mode='w')
        
        logger.info(f"Successfully saved stratified sample to {output_file}")
        
        # Compute and save hash for verification
        file_hash = compute_file_hash(output_file)
        checksum_data = {
            str(output_file): file_hash,
            "algorithm": "sha256",
            "sample_size": len(stratified_samples),
            "stratification_column": stratification_col
        }
        save_checksum(checksum_data)
        
        return output_file
        
    except Exception as e:
        logger.error(f"Failed to download and stratify dataset: {str(e)}")
        raise RuntimeError(f"Dataset download failed: {str(e)}")

def main():
    """Main entry point for downloading stratified sample."""
    setup_logging()
    
    logger.info("Starting stratified sample download for OC20 dataset")
    
    try:
        output_path = download_stratified_sample()
        logger.info(f"Download complete. Output saved to: {output_path}")
        
        # Verify the downloaded file
        if verify_downloaded_data(output_path):
            logger.info("Download verification passed")
        else:
            logger.error("Download verification failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
