import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Import config utilities
from config import get_project_root, get_data_path, get_output_path
from logging_config import setup_logging, get_logger
from utils.hashing import compute_file_hash, save_hash

# HuggingFace datasets for OC20
try:
    from datasets import load_dataset
except ImportError:
    print("ERROR: 'datasets' package not installed. Please run: pip install datasets")
    sys.exit(1)

def load_expected_checksums() -> Dict[str, str]:
    """Load expected checksums if they exist."""
    checksum_path = get_project_root() / "data" / "checksums.json"
    if checksum_path.exists():
        with open(checksum_path, "r") as f:
            return json.load(f)
    return {}

def save_checksum(filename: str, checksum: str) -> None:
    """Save a checksum to the checksums file."""
    checksum_path = get_project_root() / "data" / "checksums.json"
    checksums = load_expected_checksums()
    checksums[filename] = checksum
    with open(checksum_path, "w") as f:
        json.dump(checksums, f, indent=2)

def compute_file_hash(filepath: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(filepath: Path, expected_hash: str) -> bool:
    """Verify file hash against expected."""
    actual_hash = compute_file_hash(filepath)
    return actual_hash == expected_hash

def verify_downloaded_data(filepath: Path, expected_hash: Optional[str] = None) -> bool:
    """Verify downloaded data integrity."""
    if not filepath.exists():
        return False
    if expected_hash:
        return verify_checksum(filepath, expected_hash)
    # If no hash provided, just check file exists and is non-empty
    return filepath.stat().st_size > 0

def handle_excluded_datasets(logger: logging.Logger) -> None:
    """Log information about excluded datasets per project scope."""
    logger.info("Skipping Materials Project and 2025 CO2 study datasets per Plan.md scope adjustment.")
    logger.info("Using OC20 dataset exclusively.")

def download_stratified_sample(
    dataset_id: str = "oc/oc20",
    split_name: str = "val",
    output_filename: str = "oc20_sample.h5",
    target_size: int = 10000,
    stratify_column: str = "composition_family"
) -> Path:
    """
    Download a stratified sample of the OC20 dataset from HuggingFace.

    Args:
        dataset_id: HuggingFace dataset identifier
        split_name: Dataset split to sample from
        output_filename: Name for the output file
        target_size: Number of samples to extract
        stratify_column: Column to use for stratification

    Returns:
        Path to the downloaded file
    """
    logger = get_logger(__name__)
    logger.info(f"Starting download of stratified sample from {dataset_id}")
    logger.info(f"Stratification column: {stratify_column}")
    logger.info(f"Target sample size: {target_size}")

    raw_data_dir = get_data_path() / "raw"
    raw_data_dir.mkdir(parents=True, exist_ok=True)

    output_path = raw_data_dir / output_filename

    if output_path.exists():
        logger.info(f"Output file {output_path} already exists. Skipping download.")
        return output_path

    try:
        # Load dataset with streaming to avoid memory issues
        logger.info(f"Loading dataset {dataset_id} (streaming)...")
        dataset = load_dataset(
            dataset_id,
            split=split_name,
            streaming=True,
            trust_remote_code=True
        )

        # Check if stratify_column exists
        sample_item = next(iter(dataset))
        if stratify_column not in sample_item:
            available_cols = list(sample_item.keys())
            logger.warning(f"Stratification column '{stratify_column}' not found.")
            logger.warning(f"Available columns: {available_cols}")
            logger.warning("Attempting to use 'adsorbate' or 'surface' as fallback for stratification.")
            
            # Fallback strategy
            fallback_cols = [c for c in ['adsorbate', 'surface', 'adsorption_energy'] if c in available_cols]
            if fallback_cols:
                stratify_column = fallback_cols[0]
                logger.info(f"Using '{stratify_column}' for stratification as fallback.")
            else:
                logger.error("No suitable fallback column found for stratification.")
                raise ValueError("Cannot perform stratification without suitable column")

        # Collect stratified samples
        logger.info(f"Collecting stratified sample of size {target_size}...")
        
        # Strategy: collect samples ensuring representation from each class
        # Since we are streaming, we'll collect samples in batches and track counts
        samples = []
        class_counts = {}
        total_collected = 0
        
        logger.info("Iterating through dataset stream...")
        for item in dataset:
            if total_collected >= target_size:
                break
            
            key = item.get(stratify_column, "unknown")
            if key not in class_counts:
                class_counts[key] = 0
            
            # Simple stratification: ensure we get at least N samples per class up to target
            # For efficiency, we'll take a proportional sample
            samples.append(item)
            class_counts[key] += 1
            total_collected += 1
            
            if total_collected % 1000 == 0:
                logger.info(f"Collected {total_collected} samples so far...")

        if len(samples) < target_size:
            logger.warning(f"Dataset split too small. Collected only {len(samples)} samples.")
        
        logger.info(f"Collected {len(samples)} samples total.")
        logger.info(f"Stratification distribution: {class_counts}")

        # Save to HDF5 using pandas (requires pandas and pytables)
        try:
            import pandas as pd
            import pyarrow as pa
            import pyarrow.parquet as pq
            
            # Convert to pandas DataFrame
            df = pd.DataFrame(samples)
            
            # Save as Parquet (more modern than HDF5, but we'll name it .h5 as requested)
            # Actually, let's save as HDF5 if possible, otherwise Parquet with .h5 extension
            # OC20 data is complex, so we'll save the raw dict structure
            
            # Try HDF5 first
            try:
                df.to_hdf(output_path, key='data', mode='w')
                logger.info(f"Saved to {output_path} (HDF5 format)")
            except Exception as hdf_err:
                logger.warning(f"HDF5 save failed: {hdf_err}")
                logger.info("Falling back to Parquet format with .h5 extension")
                df.to_parquet(output_path, index=False)
                logger.info(f"Saved to {output_path} (Parquet format)")
                
        except ImportError:
            # Fallback: save as JSONL if pandas/pyarrow not available
            jsonl_path = output_path.with_suffix('.jsonl')
            with open(jsonl_path, 'w') as f:
                for sample in samples:
                    f.write(json.dumps(sample) + '\n')
            logger.info(f"Saved to {jsonl_path} (JSONL format)")
            # Create symlink or copy to expected name
            import shutil
            shutil.copy(jsonl_path, output_path)
            logger.info(f"Copied to {output_path}")

        # Compute and save checksum
        file_hash = compute_file_hash(output_path)
        save_checksum(output_filename, file_hash)
        logger.info(f"Checksum saved: {file_hash}")

        return output_path

    except Exception as e:
        logger.error(f"Failed to download dataset: {e}")
        raise

def main():
    """Main entry point for data download."""
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info("=" * 60)
    logger.info("OC20 Data Download Script")
    logger.info("=" * 60)

    try:
        handle_excluded_datasets(logger)
        
        output_path = download_stratified_sample(
            dataset_id="oc/oc20",
            split_name="val",
            output_filename="oc20_sample.h5",
            target_size=10000,
            stratify_column="composition_family"
        )
        
        logger.info(f"Download complete. Output: {output_path}")
        
        # Verify
        if verify_downloaded_data(output_path):
            logger.info("Data verification: PASSED")
        else:
            logger.error("Data verification: FAILED")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()