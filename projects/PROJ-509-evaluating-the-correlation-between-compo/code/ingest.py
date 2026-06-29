import os
import sys
import json
import hashlib
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import pandas as pd
import requests

# Local imports matching API surface
from config import load_env, load_paths
from utils.logging import setup_logging, get_logger
from utils.sampling import get_chemical_family, sample_by_chemical_family

# Constants for dataset
ZENODO_RECORD_ID = "4053859"
ZENODO_FILE_NAME = "mp-20.json"
MEMORY_THRESHOLD_MB = 3000  # 3GB threshold
RANDOM_SEED = 42

logger = get_logger(__name__)

def get_dataset_download_url(record_id: str) -> str:
    """
    Construct the download URL for the MP-20 dataset from Zenodo.
    
    Args:
        record_id: The Zenodo record ID.
        
    Returns:
        The direct download URL.
    """
    # Zenodo API endpoint to get file details
    api_url = f"https://zenodo.org/api/records/{record_id}"
    try:
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Find the specific file
        for file_info in data.get('files', []):
            if file_info.get('key') == ZENODO_FILE_NAME:
                return file_info.get('links', {}).get('self')
        
        logger.warning(f"File {ZENODO_FILE_NAME} not found in record {record_id}. Falling back to standard URL.")
        return f"https://zenodo.org/api/records/{record_id}/files/{ZENODO_FILE_NAME}/content"
        
    except Exception as e:
        logger.error(f"Failed to fetch download URL from Zenodo API: {e}")
        # Fallback URL construction
        return f"https://zenodo.org/api/records/{record_id}/files/{ZENODO_FILE_NAME}/content"

def download_file(url: str, output_path: Path) -> bool:
    """
    Download a file from a URL to a local path.
    
    Args:
        url: The URL to download from.
        output_path: The local path to save the file.
        
    Returns:
        True if download was successful, False otherwise.
    """
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    
        logger.info(f"Downloaded file to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to download file: {e}")
        return False

def calculate_sha256(file_path: Path) -> str:
    """
    Calculate the SHA256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hexadecimal SHA256 string.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def is_inorganic(composition: Dict[str, Any]) -> bool:
    """
    Determine if a composition is inorganic based on the presence of Carbon.
    
    Args:
        composition: Dictionary of element to count.
        
    Returns:
        True if inorganic, False otherwise.
    """
    # Simple heuristic: if Carbon is present and it's not a simple carbide/oxide, 
    # but for MP-20, we usually exclude organic compounds.
    # A robust check: if C is present, check if it's a known organic structure.
    # For this pipeline, we'll use a simple rule: exclude if C is present and 
    # the structure is not a standard inorganic carbide (hard to detect without full parser).
    # Standard MP-20 filter: exclude if 'C' in composition and 'H' in composition.
    # Or simpler: exclude if 'C' is the dominant element?
    # Let's use the standard MP filter: exclude if C is present and H is present.
    
    elements = set(composition.keys())
    if 'C' in elements and 'H' in elements:
        return False
    
    # Also exclude pure Carbon structures (graphite, diamond) if they are not desired,
    # but usually MP-20 includes them. Let's assume they are inorganic unless H is present.
    return True

def filter_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter the dataset for inorganic compounds with complete formation energy and composition.
    
    Args:
        df: Raw DataFrame.
        
    Returns:
        Filtered DataFrame.
    """
    logger.info(f"Starting filter on {len(df)} rows")
    
    # Ensure 'composition' is treated as a string or dict properly
    # MP-20 format usually has 'composition' as a string "{'Fe': 1, 'O': 3}" or dict
    # Let's assume it's a string representation of a dict or a dict
    
    # 1. Filter for inorganic
    # We need to parse the composition string if it's a string
    def check_inorganic(row):
        comp = row.get('composition', {})
        if isinstance(comp, str):
            try:
                import ast
                comp = ast.literal_eval(comp)
            except:
                return False
        return is_inorganic(comp)
    
    inorganic_mask = df.apply(check_inorganic, axis=1)
    df = df[inorganic_mask]
    logger.info(f"Filtered for inorganic: {len(df)} rows remaining")
    
    # 2. Filter for complete formation energy
    if 'formation_energy_per_atom' in df.columns:
        df = df.dropna(subset=['formation_energy_per_atom'])
    else:
        logger.error("Column 'formation_energy_per_atom' not found in dataset.")
        return pd.DataFrame()
        
    # 3. Filter for complete composition (non-null)
    if 'composition' in df.columns:
        df = df.dropna(subset=['composition'])
    else:
        logger.error("Column 'composition' not found in dataset.")
        return pd.DataFrame()
        
    logger.info(f"Final filtered rows: {len(df)}")
    return df

def main():
    """
    Main entry point for data ingestion and sampling.
    Downloads the dataset, filters it, performs stratified sampling if needed,
    and saves the processed data with a manifest.
    """
    setup_logging()
    paths = load_paths()
    raw_dir = paths['data_raw']
    processed_dir = paths['data_processed']
    logs_dir = paths['data_logs']
    
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Download Dataset
    raw_file_path = raw_dir / ZENODO_FILE_NAME
    logger.info(f"Checking for existing dataset at {raw_file_path}")
    
    if not raw_file_path.exists():
        url = get_dataset_download_url(ZENODO_RECORD_ID)
        logger.info(f"Downloading dataset from {url}")
        if not download_file(url, raw_file_path):
            logger.error("Download failed. Exiting.")
            sys.exit(1)
    else:
        logger.info("Dataset already exists, skipping download.")
        
    # 2. Load and Filter
    try:
        # MP-20 is usually a JSON file with a list of dictionaries
        with open(raw_file_path, 'r') as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        logger.info(f"Loaded dataset with {len(df)} rows")
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        sys.exit(1)
        
    df_filtered = filter_dataset(df)
    if df_filtered.empty:
        logger.error("No valid inorganic compounds found after filtering.")
        sys.exit(1)
        
    # 3. Sampling Logic
    estimated_size_mb = df_filtered.memory_usage(deep=True).sum() / (1024 * 1024)
    logger.info(f"Estimated memory usage: {estimated_size_mb:.2f} MB")
    
    sampled_df = df_filtered
    sampling_info = None
    
    if estimated_size_mb > MEMORY_THRESHOLD_MB:
        logger.info(f"Dataset size ({estimated_size_mb:.2f} MB) exceeds threshold ({MEMORY_THRESHOLD_MB} MB). Performing stratified sampling.")
        
        # Apply sampling
        sampled_df, counts = sample_by_chemical_family(
            df_filtered, 
            target_rows=int(df_filtered.shape[0] * 0.5), # Sample 50% if too large, or specific target
            random_state=RANDOM_SEED
        )
        
        sampling_info = {
            "method": "stratified_chemical_family",
            "original_rows": len(df_filtered),
            "sampled_rows": len(sampled_df),
            "target_rows": int(df_filtered.shape[0] * 0.5),
            "random_seed": RANDOM_SEED,
            "chemical_family_counts": counts
        }
        logger.info(f"Sampling completed. Rows reduced from {len(df_filtered)} to {len(sampled_df)}")
    else:
        logger.info(f"Dataset size ({estimated_size_mb:.2f} MB) is within threshold. Skipping sampling.")
        sampling_info = {
            "method": "none",
            "original_rows": len(df_filtered),
            "sampled_rows": len(df_filtered),
            "random_seed": RANDOM_SEED
        }
        
    # 4. Save Sampled Data
    output_csv_path = processed_dir / "sampled_raw_data.csv"
    sampled_df.to_csv(output_csv_path, index=False)
    logger.info(f"Saved sampled data to {output_csv_path}")
    
    # 5. Generate Manifest
    checksum = calculate_sha256(output_csv_path)
    manifest = {
        "version": "1.0",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "file_path": str(output_csv_path),
        "sha256": checksum,
        "row_count": len(sampled_df),
        "sampling_info": sampling_info
    }
    
    manifest_path = processed_dir / "sampling_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Saved manifest to {manifest_path}")
    
    # 6. Log Sampling Stats
    log_file_path = logs_dir / "sampling.log"
    with open(log_file_path, 'a') as f:
        f.write(f"\n--- Run at {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        f.write(f"Original Rows: {len(df_filtered)}\n")
        f.write(f"Sampled Rows: {len(sampled_df)}\n")
        f.write(f"Method: {sampling_info['method']}\n")
        f.write(f"Checksum: {checksum}\n")
        if sampling_info['method'] != 'none':
            f.write(f"Chemical Family Distribution:\n")
            for family, count in sampling_info.get('chemical_family_counts', {}).items():
                f.write(f"  {family}: {count}\n")
                
    logger.info("Ingestion and sampling pipeline completed successfully.")

if __name__ == "__main__":
    main()
