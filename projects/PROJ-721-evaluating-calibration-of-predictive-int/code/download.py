import hashlib
import json
import os
import shutil
import zipfile
import logging
import requests
from pathlib import Path
import pandas as pd
from collections import Counter
from typing import List, Dict, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
M4_GITHUB_OWNER = "M4Comp"
M4_GITHUB_REPO = "M4-Dataset"
M4_GITHUB_BRANCH = "main"
M4_ZIP_FILENAME = "M4-Dataset.zip"
MANIFEST_FILENAME = "manifest.json"
BASE_URL = f"https://raw.githubusercontent.com/{M4_GITHUB_OWNER}/{M4_GITHUB_REPO}/{M4_GITHUB_BRANCH}"
DATA_DIR = Path("data")
TEMP_DIR = Path("data/tmp")
PROCESSED_DIR = DATA_DIR / "processed"

# Sampling parameters
RANDOM_SEED = 42

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, destination: Path) -> None:
    """Download a file from a URL to a destination path."""
    logger.info(f"Downloading {url} to {destination}")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    with open(destination, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    logger.info(f"Downloaded {destination}")

def load_manifest(manifest_path: Path) -> dict:
    """Load and parse the manifest JSON file."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    with open(manifest_path, "r") as f:
        return json.load(f)

def validate_checksums(manifest: dict, data_dir: Path) -> bool:
    """Validate SHA256 checksums of files against the manifest."""
    all_valid = True
    for file_entry in manifest.get("files", []):
        filename = file_entry.get("filename")
        expected_checksum = file_entry.get("sha256")
        
        if not filename or not expected_checksum:
            logger.warning(f"Skipping entry with missing filename or checksum: {file_entry}")
            continue
        
        file_path = data_dir / filename
        if not file_path.exists():
            logger.error(f"File not found for checksum validation: {file_path}")
            all_valid = False
            continue
        
        actual_checksum = calculate_sha256(file_path)
        if actual_checksum != expected_checksum:
            logger.error(f"Checksum mismatch for {filename}: expected {expected_checksum}, got {actual_checksum}")
            all_valid = False
        else:
            logger.info(f"Checksum valid for {filename}")
    
    return all_valid

def extract_zip(zip_path: Path, dest_dir: Path) -> None:
    """Extract a zip file to a destination directory."""
    logger.info(f"Extracting {zip_path} to {dest_dir}")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(dest_dir)
    logger.info("Extraction complete")

def cleanup_temp_files(temp_dir: Path) -> None:
    """Remove temporary directory and its contents."""
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
        logger.info(f"Cleaned up temporary directory: {temp_dir}")

def load_m4_metadata(data_dir: Path) -> pd.DataFrame:
    """
    Load M4 metadata from the extracted dataset.
    Expects the dataset to be extracted into data/ directory with 'M4-*.csv' files 
    and metadata files.
    """
    # M4 dataset structure: metadata is in 'M4-metadata.csv' inside the zip
    # After extraction, it should be at data_dir / 'M4-metadata.csv'
    metadata_path = data_dir / "M4-metadata.csv"
    
    if not metadata_path.exists():
        # Try to find it in subdirectories
        for file_path in data_dir.rglob("M4-metadata.csv"):
            metadata_path = file_path
            break
    
    if not metadata_path.exists():
        raise FileNotFoundError(f"M4 metadata file not found in {data_dir}")
    
    logger.info(f"Loading metadata from {metadata_path}")
    df = pd.read_csv(metadata_path)
    
    # Ensure required columns exist
    required_cols = ['Series', 'f', 'S']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Metadata missing required columns: {missing_cols}")
    
    # Rename columns for consistency
    # 'f' is frequency, 'S' is seasonality
    df = df.rename(columns={'f': 'frequency', 'S': 'seasonality'})
    
    return df

def stratified_sample_metadata(
    df: pd.DataFrame, 
    target_size: int, 
    seed: int = RANDOM_SEED
) -> pd.DataFrame:
    """
    Perform stratified sampling on metadata by frequency and seasonality.
    
    Args:
        df: DataFrame with 'frequency' and 'seasonality' columns
        target_size: Target number of samples (if None, uses 1000 as default)
        seed: Random seed for reproducibility
    
    Returns:
        DataFrame with sampled rows
    """
    if target_size is None:
        # Default to 1000 as per task description
        target_size = 1000
    
    if target_size >= len(df):
        logger.warning(f"Target size {target_size} >= dataset size {len(df)}. Returning full dataset.")
        return df.reset_index(drop=True)
    
    # Create a combined stratification key
    df = df.copy()
    df['_strata'] = df['frequency'].astype(str) + '_' + df['seasonality'].astype(str)
    
    # Calculate sample sizes per stratum
    stratum_counts = df['_strata'].value_counts()
    total_size = len(df)
    
    # Proportional allocation
    sample_sizes = (stratum_counts / total_size * target_size).round().astype(int)
    
    # Ensure we don't exceed available samples in any stratum
    for stratum, size in sample_sizes.items():
        if size > stratum_counts[stratum]:
            sample_sizes[stratum] = stratum_counts[stratum]
    
    # Adjust to hit target exactly
    current_total = sample_sizes.sum()
    if current_total < target_size:
        # Add remaining samples to largest strata
        remaining = target_size - current_total
        stratum_order = stratum_counts.sort_values(ascending=False).index
        for stratum in stratum_order:
            if remaining <= 0:
                break
            available = stratum_counts[stratum] - sample_sizes[stratum]
            add = min(available, remaining)
            sample_sizes[stratum] += add
            remaining -= add
    elif current_total > target_size:
        # Remove excess from smallest strata
        excess = current_total - target_size
        stratum_order = stratum_counts.sort_values(ascending=True).index
        for stratum in stratum_order:
            if excess <= 0:
                break
            remove = min(sample_sizes[stratum], excess)
            sample_sizes[stratum] -= remove
            excess -= remove
    
    # Perform sampling
    sampled_dfs = []
    for stratum, size in sample_sizes.items():
        stratum_df = df[df['_strata'] == stratum]
        sampled = stratum_df.sample(n=size, random_state=seed)
        sampled_dfs.append(sampled)
    
    sampled_df = pd.concat(sampled_dfs, ignore_index=True)
    sampled_df = sampled_df.drop(columns=['_strata'])
    
    return sampled_df

def compare_distributions(
    full_df: pd.DataFrame, 
    sample_df: pd.DataFrame,
    columns: List[str] = ['frequency', 'seasonality']
) -> Dict[str, Any]:
    """
    Compare distributions between full dataset and sample.
    
    Returns:
        Dictionary with distribution stats and coverage metric
    """
    result = {
        'full_distribution': {},
        'sample_distribution': {},
        'coverage': 0.0
    }
    
    for col in columns:
        full_counts = full_df[col].value_counts(normalize=True).to_dict()
        sample_counts = sample_df[col].value_counts(normalize=True).to_dict()
        
        result['full_distribution'][col] = {str(k): float(v) for k, v in full_counts.items()}
        result['sample_distribution'][col] = {str(k): float(v) for k, v in sample_counts.items()}
    
    # Calculate coverage: proportion of original distribution represented in sample
    # We use the minimum ratio of sample proportion to full proportion across all categories
    coverage_scores = []
    for col in columns:
        full_counts = full_df[col].value_counts(normalize=True)
        sample_counts = sample_df[col].value_counts(normalize=True)
        
        for category in full_counts.index:
            full_prop = full_counts[category]
            sample_prop = sample_counts.get(category, 0.0)
            if full_prop > 0:
                ratio = sample_prop / full_prop
                coverage_scores.append(ratio)
    
    result['coverage'] = float(min(coverage_scores)) if coverage_scores else 0.0
    
    return result

def generate_sampling_report(
    full_df: pd.DataFrame,
    sample_df: pd.DataFrame,
    output_path: Path
) -> Dict[str, Any]:
    """
    Generate and save sampling report.
    
    Args:
        full_df: Full metadata DataFrame
        sample_df: Sampled metadata DataFrame
        output_path: Path to save the report JSON
    
    Returns:
        Report dictionary
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Compare distributions
    comparison = compare_distributions(full_df, sample_df)
    
    # Build report
    report = {
        'sample_size': len(sample_df),
        'full_size': len(full_df),
        'sampling_ratio': len(sample_df) / len(full_df),
        'seed': RANDOM_SEED,
        'coverage': comparison['coverage'],
        'distribution_comparison': comparison,
        'sample_indices': sample_df['Series'].tolist(),
        'sample_metadata': sample_df.to_dict(orient='records')
    }
    
    # Save report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Sampling report saved to {output_path}")
    logger.info(f"Sample coverage: {report['coverage']:.4f}")
    
    return report

def main() -> None:
    """Main function to download, extract, and perform stratified sampling on M4 dataset."""
    # Ensure directories exist
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    zip_url = f"{BASE_URL}/{M4_ZIP_FILENAME}"
    manifest_url = f"{BASE_URL}/{MANIFEST_FILENAME}"
    
    zip_path = DATA_DIR / M4_ZIP_FILENAME
    manifest_path = DATA_DIR / MANIFEST_FILENAME
    report_path = PROCESSED_DIR / "sampling_report.json"

    try:
        # Download manifest
        download_file(manifest_url, manifest_path)
        
        # Load manifest
        manifest = load_manifest(manifest_path)
        
        # Check if zip already exists and validate
        if zip_path.exists():
            logger.info(f"Found existing {M4_ZIP_FILENAME}, validating checksum...")
            if validate_checksums(manifest, DATA_DIR):
                logger.info("Existing file checksum valid. Skipping download.")
            else:
                logger.warning("Existing file checksum invalid. Re-downloading.")
                zip_path.unlink()
        
        # Download zip if not present or invalid
        if not zip_path.exists():
            download_file(zip_url, zip_path)
        
        # Final validation
        if not validate_checksums(manifest, DATA_DIR):
            raise RuntimeError("Checksum validation failed after download. Aborting.")
        
        # Extract the dataset
        extract_zip(zip_path, DATA_DIR)
        
        logger.info("M4 Dataset successfully fetched and validated.")
        
        # Load metadata
        metadata_df = load_m4_metadata(DATA_DIR)
        logger.info(f"Loaded {len(metadata_df)} series from metadata")
        
        # Perform stratified sampling
        # Target size is deferred in task description, using 1000 as default
        sampled_df = stratified_sample_metadata(metadata_df, target_size=1000, seed=RANDOM_SEED)
        logger.info(f"Selected {len(sampled_df)} series for sampling")
        
        # Generate report
        report = generate_sampling_report(metadata_df, sampled_df, report_path)
        
        # Verify coverage requirement
        if report['coverage'] < 0.90:
            logger.warning(f"Coverage {report['coverage']:.4f} is below 0.90 threshold!")
        else:
            logger.info(f"Coverage {report['coverage']:.4f} meets >= 0.90 requirement")
        
        logger.info("Sampling complete.")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during download: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during dataset processing: {e}")
        raise

if __name__ == "__main__":
    main()