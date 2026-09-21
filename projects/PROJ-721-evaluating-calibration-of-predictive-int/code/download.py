"""
Data loading, validation, and sampling utilities for the M4 dataset.
Handles downloading, checksum validation, extraction, metadata loading,
and stratified sampling for the calibration evaluation pipeline.
"""
import hashlib
import json
import logging
import os
import shutil
import zipfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.special import rel_entr

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
STATE_DIR = PROJECT_ROOT / "state"

# Ensure directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, dest_path: str) -> None:
    """Download a file from a URL to a destination path."""
    import urllib.request
    logger.info(f"Downloading {url} to {dest_path}")
    try:
        urllib.request.urlretrieve(url, dest_path)
        logger.info(f"Download complete: {dest_path}")
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        raise

def load_manifest(manifest_path: str) -> Dict[str, str]:
    """Load the manifest.json file containing checksums."""
    with open(manifest_path, 'r') as f:
        return json.load(f)

def validate_checksums(
    file_path: str,
    expected_checksum: str,
    checksum_type: str = "sha256"
) -> bool:
    """Validate the checksum of a file against an expected value."""
    if checksum_type.lower() == "sha256":
        actual_checksum = calculate_sha256(file_path)
    else:
        raise ValueError(f"Unsupported checksum type: {checksum_type}")
    
    if actual_checksum != expected_checksum:
        logger.error(f"Checksum mismatch for {file_path}")
        logger.error(f"Expected: {expected_checksum}")
        logger.error(f"Actual: {actual_checksum}")
        return False
    
    logger.info(f"Checksum validation passed for {file_path}")
    return True

def extract_zip(zip_path: str, extract_dir: str) -> None:
    """Extract a ZIP file to a directory."""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    logger.info(f"Extracted {zip_path} to {extract_dir}")

def cleanup_temp_files(temp_dir: str) -> None:
    """Remove temporary files and directories."""
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        logger.info(f"Cleaned up temporary directory: {temp_dir}")

def load_m4_metadata(metadata_path: str) -> pd.DataFrame:
    """
    Load M4 dataset metadata.
    
    Args:
        metadata_path: Path to the M4 metadata file (e.g., 'M4-metadata.csv' or 'M4-Information.csv')
    
    Returns:
        pd.DataFrame containing the metadata
    
    Raises:
        ValueError: If required fields are missing
    """
    # Try common metadata file names if not specified
    if not os.path.exists(metadata_path):
        possible_names = [
            "M4-Information.csv",
            "M4-metadata.csv",
            "M4-information.csv"
        ]
        found = False
        for name in possible_names:
            potential_path = DATA_RAW_DIR / name
            if potential_path.exists():
                metadata_path = str(potential_path)
                found = True
                break
        
        if not found:
            raise FileNotFoundError(
                f"Could not find M4 metadata file. Expected at {metadata_path} "
                f"or one of {possible_names} in {DATA_RAW_DIR}"
            )
    
    # Load the metadata
    df = pd.read_csv(metadata_path)
    
    # Validate required fields
    required_fields = ['seasonality', 'frequency']
    missing_fields = [f for f in required_fields if f not in df.columns]
    
    if missing_fields:
        raise ValueError(
            f"Missing required metadata fields: {missing_fields}. "
            f"Available columns: {list(df.columns)}"
        )
    
    logger.info(f"Loaded M4 metadata with {len(df)} series")
    return df

def compare_distributions(
    full_distribution: pd.Series,
    sample_distribution: pd.Series
) -> float:
    """
    Calculate KL divergence between two distributions.
    
    Args:
        full_distribution: Distribution of the full dataset (normalized counts)
        sample_distribution: Distribution of the sample (normalized counts)
    
    Returns:
        KL divergence value
    """
    # Ensure distributions are aligned
    all_categories = full_distribution.index.union(sample_distribution.index)
    
    full_norm = full_distribution.reindex(all_categories, fill_value=0) / len(full_distribution)
    sample_norm = sample_distribution.reindex(all_categories, fill_value=0) / len(sample_distribution)
    
    # Calculate KL divergence: sum(p(x) * log(p(x) / q(x)))
    # Avoid log(0) by filtering out zero probabilities in p
    mask = full_norm > 0
    kl_div = np.sum(full_norm[mask] * np.log(full_norm[mask] / sample_norm[mask]))
    
    return kl_div

def stratified_sample_metadata(
    metadata_df: pd.DataFrame,
    sample_size: int = 1000,
    stratify_cols: List[str] = ['frequency', 'seasonality'],
    seed: int = 42
) -> Tuple[pd.DataFrame, float, Dict[str, Any]]:
    """
    Perform stratified sampling on M4 metadata to select representative series.
    
    Args:
        metadata_df: DataFrame containing M4 metadata
        sample_size: Target number of samples (up to 1000)
        stratify_cols: Columns to use for stratification
        seed: Random seed for reproducibility
    
    Returns:
        Tuple of (sampled_df, kl_divergence, report_dict)
    
    Raises:
        ValueError: If stratification fails or sample size exceeds available
    """
    np.random.seed(seed)
    
    # Check if we have enough data
    total_available = len(metadata_df)
    actual_sample_size = min(sample_size, total_available)
    
    if actual_sample_size < sample_size:
        logger.warning(
            f"Requested {sample_size} samples but only {total_available} available. "
            f"Using {actual_sample_size}."
        )
    
    # Perform stratified sampling
    try:
        sampled_df = metadata_df.groupby(stratify_cols, group_keys=False).apply(
            lambda x: x.sample(
                n=min(len(x), int(np.ceil(len(x) * actual_sample_size / len(metadata_df)))),
                random_state=seed
            )
        ).reset_index(drop=True)
    except Exception as e:
        # Fallback: simple random sampling if stratification fails
        logger.warning(f"Stratified sampling failed: {e}. Using simple random sampling.")
        sampled_df = metadata_df.sample(n=actual_sample_size, random_state=seed)
    
    # Ensure we don't exceed the target
    if len(sampled_df) > actual_sample_size:
        sampled_df = sampled_df.sample(n=actual_sample_size, random_state=seed)
    
    # Calculate distributions
    full_dist = metadata_df.groupby(stratify_cols).size()
    sample_dist = sampled_df.groupby(stratify_cols).size()
    
    # Calculate KL divergence
    kl_div = compare_distributions(full_dist, sample_dist)
    
    # Generate report
    report = {
        "total_series": total_available,
        "sample_size": len(sampled_df),
        "stratification_columns": stratify_cols,
        "kl_divergence": float(kl_div),
        "full_distribution": {
            str(k): int(v) for k, v in full_dist.items()
        },
        "sample_distribution": {
            str(k): int(v) for k, v in sample_dist.items()
        }
    }
    
    logger.info(f"Stratified sampling complete. KL divergence: {kl_div:.4f}")
    logger.info(f"Sample size: {len(sampled_df)}")
    
    return sampled_df, kl_div, report

def generate_sampling_report(
    report: Dict[str, Any],
    output_path: str
) -> None:
    """Save the sampling report to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    logger.info(f"Sampling report saved to {output_path}")

def main():
    """
    Main entry point for data loading and sampling.
    
    This function:
    1. Loads M4 metadata
    2. Validates required fields
    3. Performs stratified sampling
    4. Verifies KL divergence < 0.1
    5. Saves sample indices to CSV
    """
    # Load metadata
    try:
        metadata_df = load_m4_metadata(None)  # Auto-detect path
    except FileNotFoundError as e:
        logger.error(f"Metadata loading failed: {e}")
        raise
    except ValueError as e:
        logger.error(f"Metadata validation failed: {e}")
        raise
    
    # Perform stratified sampling
    sample_df, kl_div, report = stratified_sample_metadata(
        metadata_df,
        sample_size=1000,
        stratify_cols=['frequency', 'seasonality'],
        seed=42
    )
    
    # Verify KL divergence
    if kl_div >= 0.1:
        logger.error(f"KL divergence {kl_div:.4f} exceeds threshold 0.1")
        raise ValueError(
            f"Sampling distribution too different from full dataset. "
            f"KL divergence: {kl_div:.4f}, threshold: 0.1"
        )
    
    # Verify sample size
    if len(sample_df) < 1000 and len(metadata_df) >= 1000:
        logger.error(f"Sample size {len(sample_df)} is less than target 1000")
        raise ValueError(f"Failed to select 1000 representative series")
    
    # Save sample indices
    output_path = DATA_PROCESSED_DIR / "sample_indices.csv"
    sample_df[['series_id']].to_csv(output_path, index=False)
    logger.info(f"Saved {len(sample_df)} series IDs to {output_path}")
    
    # Save sampling report
    report_path = STATE_DIR / "sampling_report.json"
    generate_sampling_report(report, str(report_path))
    
    # Verify output
    assert output_path.exists(), f"Output file {output_path} was not created"
    assert len(sample_df) >= 1000 or len(sample_df) == len(metadata_df), \
        f"Sample size {len(sample_df)} does not meet requirements"
    assert kl_div < 0.1, f"KL divergence {kl_div} exceeds threshold"
    
    print(f"Task T013a completed successfully.")
    print(f"Sample size: {len(sample_df)}")
    print(f"KL divergence: {kl_div:.4f}")
    print(f"Output: {output_path}")

if __name__ == "__main__":
    main()
