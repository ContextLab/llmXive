import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from huggingface_hub import snapshot_download, hf_hub_download
import pandas as pd
import numpy as np

# Import project utilities
from config import get_project_root, get_data_path, get_output_path
from utils.hashing import compute_file_hash, save_hash
from utils.validation import verify_data_checksum

logger = logging.getLogger(__name__)

REPO_ID = "oc/oc20-sample-v1"
STRATIFY_COLUMN = "composition_family"
OUTPUT_FILENAME = "oc20_sample.h5"
TARGET_SIZE = 5000  # Target sample size for the stratified subset

def handle_excluded_datasets():
    """
    Log exclusion of external datasets (Materials Project, 2025 CO2 study)
    as per Plan.md 'Critical Scope Adjustment'.
    """
    logger.info("Handling excluded datasets: Materials Project and 2025 CO2 study are excluded per Plan.md scope adjustment.")
    # This function exists to satisfy T012 logic if called, but T012 is separate.
    # Here we just ensure the logging infrastructure acknowledges the scope.

def verify_checksum(filepath: Path, expected_hash: str) -> bool:
    """Verify the SHA256 checksum of a file."""
    actual_hash = compute_file_hash(filepath)
    if actual_hash != expected_hash:
        logger.error(f"Checksum mismatch for {filepath}: expected {expected_hash}, got {actual_hash}")
        return False
    logger.info(f"Checksum verified for {filepath}")
    return True

def save_checksum(filepath: Path, hash_value: str, checksum_file: Path):
    """Save the checksum to a JSON file."""
    data = {
        "file": filepath.name,
        "sha256": hash_value,
        "timestamp": str(Path(filepath).stat().st_mtime)
    }
    with open(checksum_file, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Checksum saved to {checksum_file}")

def load_expected_checksum(checksum_file: Path) -> Optional[str]:
    """Load expected checksum from file."""
    if checksum_file.exists():
        with open(checksum_file, 'r') as f:
            data = json.load(f)
            return data.get("sha256")
    return None

def verify_downloaded_data(filepath: Path, expected_hash: Optional[str] = None) -> bool:
    """
    Verify downloaded data. If expected_hash is provided, compare against it.
    Otherwise, just verify file integrity (non-empty).
    """
    if not filepath.exists():
        logger.error(f"Downloaded file not found: {filepath}")
        return False

    if expected_hash:
        return verify_checksum(filepath, expected_hash)
    
    # Basic integrity check
    if filepath.stat().st_size == 0:
        logger.error(f"Downloaded file is empty: {filepath}")
        return False
    
    logger.info(f"File downloaded and exists: {filepath} (size: {filepath.stat().st_size} bytes)")
    return True

def download_stratified_sample(output_path: Path, target_size: int = TARGET_SIZE):
    """
    Download the OC20 sample from HuggingFace, perform stratified sampling,
    and save as HDF5.
    
    This function:
    1. Downloads the full dataset (or a shard) from 'oc/oc20-sample-v1'.
    2. Loads it into memory (chunked if necessary).
    3. Performs stratified sampling by 'composition_family'.
    4. Saves the result to HDF5.
    
    Note: If the dataset is too large for memory, we stream and sample.
    However, for a 'sample' repo, we assume it fits or is manageable.
    """
    logger.info(f"Starting download of stratified sample from {REPO_ID}")
    
    # Determine local cache path for the download
    # We download to a temp location first or directly to data/raw if we handle the logic carefully.
    # To ensure we don't corrupt existing files, we download to a temp file then move.
    temp_dir = output_path.parent / ".temp_download"
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # Attempt to download the dataset. 
        # We try to download the parquet or csv files if available, or the whole repo.
        # Assuming the repo contains a dataset file like 'data.parquet' or similar.
        # If the repo is a 'dataset' hub repo, we might use load_dataset, but snapshot_download is safer for raw files.
        
        # Strategy: Download the specific file if known, else try to list and pick the largest data file.
        # For OC20 sample, let's assume a file named 'oc20_sample.parquet' or 'data.csv' exists.
        # If the repo is the actual OC20 sample, it might be large.
        
        # Fallback: Use huggingface_hub to list files and download the data file.
        # Since we cannot guarantee the exact filename without inspecting the repo,
        # we will try to download the repo content to a local dir, then process.
        
        local_cache_dir = snapshot_download(
            repo_id=REPO_ID,
            repo_type="dataset",
            local_dir=temp_dir,
            local_dir_use_symlinks=False
        )
        
        logger.info(f"Downloaded repo to {local_cache_dir}")
        
        # Find the data file (parquet, csv, json)
        data_files = list(temp_dir.rglob("*"))
        data_file = None
        for f in data_files:
            if f.is_file() and f.suffix in ['.parquet', '.csv', '.json', '.h5', '.hdf5']:
                # Skip metadata files if possible, prefer data files
                if 'README' not in f.name and 'LICENSE' not in f.name:
                    data_file = f
                    break
        
        if not data_file:
            # Fallback: take the first non-hidden file
            for f in data_files:
                if f.is_file() and not f.name.startswith('.'):
                    data_file = f
                    break
        
        if not data_file:
            raise FileNotFoundError("No data file found in downloaded repository.")
        
        logger.info(f"Found data file: {data_file}")
        
        # Load data
        df = None
        if data_file.suffix == '.parquet':
            df = pd.read_parquet(data_file)
        elif data_file.suffix == '.csv':
            df = pd.read_csv(data_file)
        elif data_file.suffix in ['.json', '.jsonl']:
            df = pd.read_json(data_file, lines=True)
        elif data_file.suffix in ['.h5', '.hdf5']:
            df = pd.read_hdf(data_file)
        else:
            # Try reading as CSV as default
            try:
                df = pd.read_csv(data_file)
            except Exception:
                raise ValueError(f"Unsupported file format: {data_file.suffix}")
        
        logger.info(f"Loaded dataset with shape: {df.shape}")
        
        # Verify stratification column exists
        if STRATIFY_COLUMN not in df.columns:
            available_cols = list(df.columns)
            # Try to find a similar column if exact name is missing
            # Common variations: 'family', 'composition', 'catalyst_family'
            candidates = [c for c in available_cols if 'family' in c.lower() or 'composition' in c.lower()]
            if candidates:
                logger.warning(f"Column '{STRATIFY_COLUMN}' not found. Attempting to use '{candidates[0]}' for stratification.")
                strat_col = candidates[0]
            else:
                raise KeyError(f"Stratification column '{STRATIFY_COLUMN}' not found in dataset. Available: {available_cols}")
        else:
            strat_col = STRATIFY_COLUMN

        # Perform Stratified Sampling
        # Ensure we don't request more than available per group
        # We want a total of 'target_size' rows.
        # Calculate sample size per group proportional to group size.
        
        group_counts = df[strat_col].value_counts()
        total_rows = len(df)
        
        # Calculate proportional sizes
        # If target_size > total_rows, we just take the whole dataset
        if target_size >= total_rows:
            logger.warning(f"Target size ({target_size}) >= total rows ({total_rows}). Taking full dataset.")
            sampled_df = df
        else:
            # Calculate sample size for each group
            sample_sizes = (group_counts / total_rows * target_size).astype(int)
            
            # Ensure at least 1 sample per group if possible, unless group is too small
            # Adjust if sum(sample_sizes) != target_size due to rounding
            while sample_sizes.sum() < target_size:
                # Find the group with the largest remainder or just add to largest
                sample_sizes = sample_sizes + 1
                if sample_sizes.sum() > target_size:
                    sample_sizes[-1] -= 1 # Adjust last
            
            # Cap at group size
            for group, size in sample_sizes.items():
                if size > group_counts[group]:
                    sample_sizes[group] = group_counts[group]
            
            # Re-sum and adjust if we overshot due to capping
            current_sum = sample_sizes.sum()
            if current_sum < target_size:
                # We can't reach target_size, take what we can
                logger.warning(f"Could not reach target size {target_size}. Taking {current_sum} rows.")
            
            # Perform sampling
            sampled_df = df.groupby(strat_col, group_keys=False).apply(
                lambda x: x.sample(n=min(sample_sizes.get(x.name, 0), len(x)), random_state=42)
            )
            # Reset index
            sampled_df = sampled_df.reset_index(drop=True)
        
        logger.info(f"Stratified sampling complete. New shape: {sampled_df.shape}")
        
        # Save to HDF5
        output_path.parent.mkdir(parents=True, exist_ok=True)
        sampled_df.to_hdf(output_path, key='data', mode='w')
        logger.info(f"Saved stratified sample to {output_path}")
        
        # Compute and save checksum
        checksum = compute_file_hash(output_path)
        checksum_file = output_path.parent / f"{output_path.name}.sha256"
        save_checksum(output_path, checksum, checksum_file)
        
        return True

    except Exception as e:
        logger.error(f"Failed to download or process dataset: {e}", exc_info=True)
        raise
    finally:
        # Cleanup temp directory
        if temp_dir.exists():
            import shutil
            shutil.rmtree(temp_dir)

def main():
    """Main entry point for data download."""
    # Setup logging
    from logging_config import setup_logging
    setup_logging()
    
    project_root = get_project_root()
    data_path = get_data_path()
    
    output_file = data_path / "raw" / OUTPUT_FILENAME
    
    logger.info(f"Project root: {project_root}")
    logger.info(f"Data path: {data_path}")
    logger.info(f"Output file: {output_file}")
    
    # Ensure raw directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Handle excluded datasets (T012 logic placeholder)
    handle_excluded_datasets()
    
    # Download and process
    try:
        success = download_stratified_sample(output_file, TARGET_SIZE)
        if success:
            logger.info("Data download and stratification completed successfully.")
        else:
            logger.error("Data download failed.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Critical error in download pipeline: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
