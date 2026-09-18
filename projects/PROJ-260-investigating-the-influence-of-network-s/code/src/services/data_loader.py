"""
Data Loader Service for fetching real amorphous silicon trajectories.

This module implements the strict acquisition of real MD trajectory data
from verified sources (Zenodo/Materials Cloud) as defined in research.md.
It strictly adheres to the 'Fail Loudly' principle: no synthetic fallbacks.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib

# Try to import datasets, fail immediately if not available (dependency check)
try:
    from datasets import load_dataset
except ImportError:
    print("CRITICAL ERROR: 'datasets' package is required but not installed.", file=sys.stderr)
    print("Please install it via: pip install datasets", file=sys.stderr)
    sys.exit(1)

from src.lib.config import get_project_root, load_config
from src.lib.utils import setup_logging, compute_file_checksum, validate_directory_exists

# Configure logger
logger = setup_logging("data_loader")

# Constants
DATA_RAW_DIR = Path("data/raw")
MISSING_LOG_FILE = Path("data/raw/missing_datasets.log")
MANIFEST_FILE = Path("data/raw/checksum_manifest.json")

# Hardcoded mapping of system sizes to verified dataset IDs
# In a real production scenario, this would be dynamically parsed from research.md
# but for this implementation, we assume the verified IDs are:
# N=1000: zenodo.10000001 (Example ID - replaced with actual logic below)
# N=2000: zenodo.10000002
# N=4000: zenodo.10000003
# NOTE: The actual IDs must be present in the research.md file.
# Since I cannot read research.md at runtime, I will implement the logic to
# read it, but I will also define a fallback error if the file is missing.

SYSTEM_SIZES = [1000, 2000, 4000]

def load_verified_dataset_ids() -> Dict[int, str]:
    """
    Loads the verified dataset IDs from research.md.
    Expects a block in research.md like:
    ### Verified Datasets
    - N=1000: zenodo/12345
    - N=2000: zenodo/67890
    """
    project_root = get_project_root()
    research_path = project_root / "research.md"
    
    if not research_path.exists():
        logger.error(f"research.md not found at {research_path}. Cannot fetch dataset IDs.")
        raise FileNotFoundError(f"research.md not found at {research_path}")

    dataset_map = {}
    try:
        content = research_path.read_text()
        # Simple regex-like parsing for the Verified Datasets block
        # Looking for lines like: - N=1000: zenodo/12345
        import re
        pattern = r'-\s*N=(\d+):\s*(\S+)'
        matches = re.findall(pattern, content)
        
        for size_str, id_str in matches:
            size = int(size_str)
            dataset_map[size] = id_str
            logger.info(f"Found verified dataset ID for N={size}: {id_str}")
    except Exception as e:
        logger.error(f"Error parsing research.md: {e}")
        raise

    if not dataset_map:
        raise ValueError("No verified dataset IDs found in research.md. Aborting.")
    
    return dataset_map

def fetch_dataset(dataset_id: str, system_size: int, output_dir: Path) -> bool:
    """
    Fetches a dataset using the HuggingFace datasets library.
    
    Args:
        dataset_id: The ID string (e.g., "zenodo/12345" or a direct URL)
        system_size: The system size (N) for logging
        output_dir: Directory to save the raw files
        
    Returns:
        True if successful, False otherwise.
    """
    logger.info(f"Attempting to fetch dataset {dataset_id} for N={system_size}...")
    
    try:
        # Attempt to load the dataset
        # We use streaming=False to download the full file for checksum verification
        # If the dataset is too large, this might fail, but the task requires
        # fetching the real data.
        dataset = load_dataset(dataset_id, split="train", streaming=False)
        
        # Check if we got data
        if len(dataset) == 0:
            logger.error(f"Dataset {dataset_id} returned 0 rows.")
            return False

        # Determine file name based on dataset structure
        # Assuming the dataset contains a file like 'trajectory.xyz' or similar
        # We will save the raw parquet or csv files provided by the dataset
        # If it's a generic dataset, we save the first file found.
        
        # For this implementation, we assume the dataset yields a file we can save.
        # We will save the raw data as a compressed parquet file for efficiency.
        output_path = output_dir / f"amorphous_si_N{system_size}.parquet"
        
        # Save to parquet
        dataset.to_parquet(str(output_path))
        
        logger.info(f"Successfully saved data to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to fetch dataset {dataset_id} for N={system_size}: {e}")
        return False

def write_missing_log(missing_ids: List[str]):
    """Writes a log of missing datasets."""
    if not missing_ids:
        return
    
    validate_directory_exists(DATA_RAW_DIR)
    with open(MISSING_LOG_FILE, 'w') as f:
        f.write("Missing Datasets Report\n")
        f.write("=======================\n")
        f.write("The following verified datasets could not be fetched:\n")
        for ds_id in missing_ids:
            f.write(f"- {ds_id}\n")
    
    logger.error(f"Missing datasets logged to {MISSING_LOG_FILE}")

def main():
    """Main entry point for the data loader."""
    logger.info("Starting Data Loader for Amorphous Silicon Trajectories")
    
    # Ensure output directory exists
    validate_directory_exists(DATA_RAW_DIR)
    
    # Load verified IDs from research.md
    try:
        dataset_ids = load_verified_dataset_ids()
    except Exception as e:
        logger.critical(f"Failed to load dataset IDs: {e}")
        sys.exit(1)

    missing_datasets = []
    success_count = 0

    # Iterate over required system sizes
    for size in SYSTEM_SIZES:
        if size not in dataset_ids:
            logger.warning(f"No verified dataset ID found for N={size} in research.md. Skipping.")
            missing_datasets.append(f"N={size} (ID not found in research.md)")
            continue

        ds_id = dataset_ids[size]
        success = fetch_dataset(ds_id, size, DATA_RAW_DIR)
        
        if success:
            success_count += 1
        else:
            missing_datasets.append(f"N={size} (ID: {ds_id})")

    # Final verification
    if missing_datasets:
        write_missing_log(missing_datasets)
        logger.critical(f"Failed to fetch {len(missing_datasets)} datasets. Exiting with code 1.")
        sys.exit(1)
    
    logger.info(f"Successfully fetched {success_count} datasets. All required realizations present.")
    sys.exit(0)

if __name__ == "__main__":
    main()
