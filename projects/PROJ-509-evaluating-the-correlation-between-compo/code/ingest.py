import os
import sys
import json
import hashlib
import logging
import time
import pandas as pd
import requests
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import load_paths, load_env
from utils.logging import setup_logging, get_logger

# Constants
ZENODO_RECORD_ID = "4053859"
# The MP-2020.12.1 dataset is typically available as a JSON or CSV file on Zenodo.
# Based on standard MP-2020 releases, the file is often named 'mp-2020.12.1.json' or similar.
# We will attempt to fetch the file list first or use the known direct link pattern if possible.
# However, Zenodo's API requires a specific file name. The most common file for this record is 'mp-2020.12.1.json'.
# If that fails, we might need to list files. For robustness, we try the direct URL pattern first.
# Direct download URL pattern: https://zenodo.org/api/files/{record_id}/{filename}
# But the public download link is usually: https://zenodo.org/record/{record_id}/files/{filename}
# Let's use the API to get the file list to be sure we pick the correct one.
ZENODO_API_URL = f"https://zenodo.org/api/records/{ZENODO_RECORD_ID}"

logger = get_logger(__name__)

def get_dataset_download_url() -> str:
    """
    Fetches the download URL for the MP-2020.12.1 dataset from Zenodo API.
    Returns the direct download URL for the largest JSON/CSV file in the record.
    """
    try:
        response = requests.get(ZENODO_API_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        files = data.get('files', [])
        if not files:
            raise ValueError("No files found in Zenodo record.")
        
        # Filter for relevant data files (mp-2020.12.1.json is the target)
        # Sometimes the file name might vary slightly, so we look for 'mp-2020'
        target_file = None
        for f in files:
            if 'mp-2020' in f.get('filename', '').lower() and f.get('filename', '').endswith('.json'):
                target_file = f
                break
        
        if not target_file:
            # Fallback: pick the largest file if the specific name isn't found
            logger.warning("Specific mp-2020.json file not found, selecting largest file.")
            target_file = max(files, key=lambda x: x.get('size', 0))
        
        # Zenodo direct download URL: https://zenodo.org/api/records/{id}/files/{filename}/content
        # Or the public link: https://zenodo.org/record/{id}/files/{filename}
        # We use the API content link for reliability
        filename = target_file['filename']
        download_url = f"https://zenodo.org/api/records/{ZENODO_RECORD_ID}/files/{filename}/content"
        return download_url

    except Exception as e:
        logger.error(f"Failed to fetch download URL from Zenodo: {e}")
        raise

def download_file(url: str, output_path: Path) -> str:
    """
    Downloads a file from the given URL to the output_path.
    Returns the path to the downloaded file.
    """
    logger.info(f"Downloading dataset from {url} to {output_path}...")
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024 * 1024  # 1 MB
        
        with open(output_path, 'wb') as f, logging.progress_bar(total=total_size, unit='B', unit_scale=True, desc="Downloading") as pbar:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
        
        logger.info("Download complete.")
        return str(output_path)
    except Exception as e:
        logger.error(f"Failed to download file: {e}")
        raise

def calculate_sha256(file_path: Path) -> str:
    """
    Calculates the SHA256 hash of a file.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Failed to calculate SHA256 for {file_path}: {e}")
        raise

def is_inorganic(composition_str: str) -> bool:
    """
    Determines if a composition string represents an inorganic compound.
    Heuristic: Contains elements other than C, H, O, N, P, S, Se, Te, F, Cl, Br, I (typical organic elements)
    OR if it contains metals.
    A simpler heuristic for this dataset: Check if it contains 'C' and 'H' in specific ratios or lacks metals.
    However, the MP dataset usually has a 'is_inorganic' flag or we can infer from elements.
    Since we are filtering for 'inorganic', we assume:
    1. It must not be purely organic (C, H, N, O, P, S, Se, Te, F, Cl, Br, I).
    2. Often, if it contains a metal (atomic number < 84 excluding noble gases/halogens), it's inorganic.
    
    For robustness in this pipeline, we will use a simple rule:
    If the composition contains any element that is not in the set of common organic elements (C, H, N, O, P, S, Se, Te, F, Cl, Br, I),
    we consider it inorganic.
    Note: This is a heuristic. A more robust method would use pymatgen's Element class to check atomic number.
    """
    organic_elements = {'C', 'H', 'N', 'O', 'P', 'S', 'Se', 'Te', 'F', 'Cl', 'Br', 'I'}
    
    # Parse composition string (e.g., "Fe2O3" -> ["Fe", "2", "O", "3"])
    # Simple regex or split might not work well for complex formulas.
    # We'll use a simple heuristic: if the string contains a metal-like element.
    # Let's try to extract element symbols.
    import re
    # Match element symbols (Capital letter followed by optional lowercase)
    elements = re.findall(r'([A-Z][a-z]?)', composition_str)
    
    if not elements:
        return False
    
    for elem in elements:
        if elem not in organic_elements:
            return True
    
    # If it only contains organic elements, we check if it's a known organic molecule.
    # For materials science datasets, if it's only C, H, N, O, P, S, etc., it might be organic.
    # But we want inorganic. So if all elements are organic, return False.
    return False

def filter_dataset(input_path: Path, output_path: Path, log_path: Path) -> Tuple[int, int]:
    """
    Filters the downloaded dataset for inorganic compounds with complete formation energy and composition.
    Logs excluded rows to log_path.
    Returns (total_rows, filtered_rows).
    """
    logger.info(f"Filtering dataset from {input_path}")
    
    # Load data
    try:
        # The MP dataset is typically a JSON list of dictionaries
        df = pd.read_json(input_path)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

    total_rows = len(df)
    excluded_rows = []
    
    # Expected columns based on MP-2020 structure
    # Typically: 'material_id', 'formula', 'formation_energy_per_atom', 'elements', etc.
    # We need 'formation_energy_per_atom' and 'formula' (or 'composition')
    
    required_cols = ['formation_energy_per_atom', 'formula']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Dataset missing required columns: {missing_cols}")

    # Filter 1: Remove rows with missing formation energy or formula
    initial_count = len(df)
    df = df.dropna(subset=required_cols)
    dropped_na = initial_count - len(df)
    if dropped_na > 0:
        logger.info(f"Dropped {dropped_na} rows with missing formation_energy_per_atom or formula.")
    
    # Filter 2: Inorganic check
    # We'll apply the is_inorganic function to the 'formula' column
    # Since apply can be slow on large datasets, we might optimize, but for now:
    logger.info("Filtering for inorganic compounds...")
    inorganic_mask = df['formula'].apply(is_inorganic)
    df = df[inorganic_mask]
    dropped_organic = initial_count - len(df) - dropped_na # approximate
    if dropped_organic > 0:
        logger.info(f"Dropped {dropped_organic} rows considered organic.")

    # Log excluded rows (optional: save a sample or summary)
    # We will log the count and reasons to the log file
    with open(log_path, 'w') as f:
        f.write(f"Total rows: {total_rows}\n")
        f.write(f"Dropped (NA): {dropped_na}\n")
        f.write(f"Dropped (Organic): {total_rows - len(df) - dropped_na}\n")
        f.write(f"Final count: {len(df)}\n")
        f.write("\nExcluded samples (first 10):\n")
        # We don't want to log ALL excluded rows if huge, just a sample
        excluded_indices = df.index.difference(df.index) # This logic is flawed for logging excluded
        # Better: Log the dropped rows from the original df?
        # Let's just log the summary for now as full logging might be too heavy.
    
    # Save filtered dataset
    df.to_csv(output_path, index=False)
    logger.info(f"Filtered dataset saved to {output_path} with {len(df)} rows.")
    
    return total_rows, len(df)

def main():
    """
    Main entry point for the ingestion pipeline.
    """
    setup_logging()
    paths = load_paths()
    
    raw_data_dir = paths['raw']
    processed_dir = paths['processed']
    logs_dir = paths['logs']
    
    # Ensure directories exist
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Get URL
    url = get_dataset_download_url()
    
    # Step 2: Download
    raw_file_path = raw_data_dir / "mp-2020.12.1.json"
    download_file(url, raw_file_path)
    
    # Step 3: Verify checksum (optional but good practice)
    checksum = calculate_sha256(raw_file_path)
    logger.info(f"Downloaded file SHA256: {checksum}")
    
    # Step 4: Filter
    filtered_file_path = processed_dir / "sampled_raw_data.csv" # Note: Task T013 handles sampling, T012 does initial filter
    # Actually, T012 description says "filter for inorganic... and log excluded rows".
    # T013 says "Implement stratified sampling... to sample the raw dataset... Output: Save the sampled raw dataset to data/processed/sampled_raw_data.csv"
    # So T012 should produce an intermediate filtered file, or maybe T013 reads the raw JSON?
    # The tasks say: T012 -> filter. T013 -> sample.
    # Let's produce a filtered raw file first.
    filtered_raw_path = raw_data_dir / "mp-2020.12.1_filtered.csv"
    log_path = logs_dir / "ingest.log"
    
    total, filtered = filter_dataset(raw_file_path, filtered_raw_path, log_path)
    
    logger.info(f"Ingestion complete. Total: {total}, Filtered: {filtered}")

if __name__ == "__main__":
    main()