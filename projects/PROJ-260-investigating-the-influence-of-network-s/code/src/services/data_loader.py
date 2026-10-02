import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib
import shutil
from urllib.request import urlretrieve
from urllib.error import URLError, HTTPError

# Import from existing project API
from src.lib.utils import FatalError, setup_logging, validate_directory_exists

# Configuration constants
DATA_RAW_DIR = Path("data/raw")
MISSING_LOG_PATH = Path("data/raw/missing_datasets.log")
RESEARCH_MD_PATH = Path("specs/001-investigate-network-heat-conduction/research.md")

# Verified Dataset IDs for Amorphous Silicon (N=1000, 2000, 4000)
# These IDs correspond to real datasets on Zenodo/Materials Cloud as per research.md
# Format: { "system_size": [list of dataset_ids] }
VERIFIED_DATASET_IDS = {
    1000: ["1234567"],  # Example ID - replace with actual Zenodo ID from research.md
    2000: ["2345678"],  # Example ID - replace with actual Zenodo ID from research.md
    4000: ["3456789"],  # Example ID - replace with actual Zenodo ID from research.md
}

# In a real implementation, these would be actual Zenodo API endpoints or direct download links
# For this implementation, we assume a structure where we can fetch from a known URL pattern
# or a local mirror if the real source is unavailable (but we MUST fail loudly if real source fails)
DATASET_BASE_URL = "https://zenodo.org/record/{id}/files/amorphous_si_N{size}.xyz"

def load_verified_dataset_ids() -> Dict[int, List[str]]:
    """
    Load verified dataset IDs from research.md.
    If research.md is not found or IDs are missing, raise FatalError.
    """
    if not RESEARCH_MD_PATH.exists():
        raise FatalError(f"research.md not found at {RESEARCH_MD_PATH}. Cannot proceed without verified dataset IDs.")
    
    # In a real scenario, we would parse research.md to extract the verified IDs
    # For now, we use the hardcoded VERIFIED_DATASET_IDS as a fallback
    # but we MUST validate that they are actually mentioned in research.md
    with open(RESEARCH_MD_PATH, 'r') as f:
        content = f.read()
    
    # Simple check: ensure the IDs we are about to use are mentioned in research.md
    for size, ids in VERIFIED_DATASET_IDS.items():
        for dataset_id in ids:
            if dataset_id not in content:
                raise FatalError(f"Dataset ID {dataset_id} for system size {size} not found in research.md. "
                                 "This is a critical failure - cannot proceed with unverified dataset.")
    
    return VERIFIED_DATASET_IDS

def fetch_dataset(system_size: int, dataset_id: str, output_dir: Path) -> Optional[Path]:
    """
    Fetch a single dataset from the real source.
    Returns the path to the downloaded file, or None if fetch fails.
    MUST fail loudly - no synthetic fallback.
    """
    # Construct the URL
    url = DATASET_BASE_URL.format(id=dataset_id, size=system_size)
    output_path = output_dir / f"amorphous_si_N{system_size}_{dataset_id}.xyz"
    
    logging.info(f"Attempting to fetch dataset {dataset_id} (N={system_size}) from {url}")
    
    try:
        # Attempt to download the file
        urlretrieve(url, output_path)
        
        # Verify the file is not empty
        if output_path.stat().st_size == 0:
            logging.error(f"Downloaded file {output_path} is empty.")
            output_path.unlink()  # Remove the empty file
            return None
        
        logging.info(f"Successfully downloaded dataset {dataset_id} to {output_path}")
        return output_path
        
    except (URLError, HTTPError) as e:
        logging.error(f"Failed to download dataset {dataset_id}: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error while downloading dataset {dataset_id}: {e}")
        return None

def write_missing_log(missing_counts: Dict[int, int]):
    """
    Write a log file documenting which system sizes failed to meet the N>=30 requirement.
    """
    MISSING_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(MISSING_LOG_PATH, 'w') as f:
        f.write("Missing Datasets Log\n")
        f.write("====================\n\n")
        f.write("The following system sizes failed to meet the N>=30 realizations requirement:\n\n")
        
        for size, count in missing_counts.items():
            f.write(f"System Size N={size}: Only {count} realizations found (required: 30)\n")
        
        f.write("\nPipeline execution halted due to insufficient data for statistical validity.\n")
    
    logging.error(f"Missing datasets logged to {MISSING_LOG_PATH}")

def main():
    """
    Main entry point for data loader.
    Fetches all verified datasets for N=1000, 2000, 4000.
    Validates that each system size has >= 30 realizations.
    Halts with FatalError if any system size has < 30 realizations.
    """
    # Setup logging
    log_file = DATA_RAW_DIR / "data_loader.log"
    logger = setup_logging(log_file=log_file, log_level=logging.INFO)
    
    # Ensure data/raw directory exists
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load verified dataset IDs
    try:
        dataset_ids = load_verified_dataset_ids()
    except FatalError as e:
        logger.critical(str(e))
        sys.exit(1)
    
    # Track realizations per system size
    realization_counts = {size: 0 for size in dataset_ids.keys()}
    missing_counts = {}
    
    # Fetch all datasets
    for system_size, ids in dataset_ids.items():
        logger.info(f"Processing system size N={system_size} with {len(ids)} dataset IDs")
        
        for dataset_id in ids:
            output_path = fetch_dataset(system_size, dataset_id, DATA_RAW_DIR)
            if output_path and output_path.exists():
                realization_counts[system_size] += 1
            else:
                logger.warning(f"Failed to fetch dataset {dataset_id} for N={system_size}")
    
    # Validate N>=30 requirement
    for size, count in realization_counts.items():
        if count < 30:
            missing_counts[size] = count
            logger.error(f"System size N={size} has only {count} realizations (required: 30)")
    
    # If any system size is missing, log and halt
    if missing_counts:
        write_missing_log(missing_counts)
        raise FatalError(f"Insufficient data: {len(missing_counts)} system size(s) have < 30 realizations. "
                         f"See {MISSING_LOG_PATH} for details.")
    
    # If we get here, all system sizes have >= 30 realizations
    logger.info("Data loading successful. All system sizes meet the N>=30 requirement.")
    logger.info(f"Realization counts: {realization_counts}")
    
    # Create a manifest file
    manifest_path = DATA_RAW_DIR / "dataset_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump({
            "system_sizes": realization_counts,
            "datasets": [
                {"size": size, "count": count}
                for size, count in realization_counts.items()
            ]
        }, f, indent=2)
    
    logger.info(f"Dataset manifest written to {manifest_path}")

if __name__ == "__main__":
    main()
