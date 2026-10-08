"""
T015a: Retrieve CLO Migratory List
Downloads the verified eBird migratory species list from the HuggingFace dataset `vvud/eb-migratory-list`.
Caches it in `data/raw/migratory_list.json` and returns a set of valid species names.
Computes SHA-256 checksum and verifies on subsequent runs.
"""
import json
import hashlib
import logging
import sys
from pathlib import Path
from typing import Set, List, Optional, Dict, Any

# Ensure src is in path for imports if running as script
if str(Path(__file__).parent.parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datasets import load_dataset
from src.config import setup_logging

# Initialize logger
logger = setup_logging("fetch_species")

# Constants
DATASET_NAME = "vvud/eb-migratory-list"
SPLIT = "train"
RAW_DIR = Path("data/raw")
PROVENANCE_DIR = Path("data/provenance")
OUTPUT_FILE = RAW_DIR / "migratory_list.json"
CHECKSUM_FILE = PROVENANCE_DIR / "ebird_checksums.json"

def compute_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_migratory_list() -> List[Dict[str, Any]]:
    """
    Download the verified eBird migratory species list from HuggingFace.
    Returns a list of dictionaries with 'species_name'.
    """
    logger.info(f"Attempting to download dataset: {DATASET_NAME}")
    try:
        # Use streaming to avoid loading full dataset into memory if large
        dataset = load_dataset(DATASET_NAME, split=SPLIT, streaming=True)
        
        # Convert to list of dicts (streaming yields dicts)
        # We assume the dataset has a 'species_name' column
        records = []
        for item in dataset:
            if 'species_name' in item:
                records.append({"species_name": item['species_name']})
            else:
                # Fallback if column name differs, though spec says 'species_name'
                # Try to find a string column that might be the name
                for key, val in item.items():
                    if isinstance(val, str):
                        records.append({"species_name": val})
                        break
        
        if not records:
            raise RuntimeError(f"Downloaded dataset from {DATASET_NAME} is empty or has no 'species_name' field.")
        
        logger.info(f"Successfully downloaded {len(records)} migratory species records.")
        return records
    except Exception as e:
        logger.error(f"Failed to fetch verified real data from {DATASET_NAME}. Aborting pipeline to prevent fabrication.")
        raise RuntimeError(f"Failed to fetch verified real data from {DATASET_NAME}. Aborting pipeline to prevent fabrication.") from e

def save_migratory_list(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Save the list of species to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved migratory list to {output_path}")

def extract_migratory_species(records: List[Dict[str, Any]]) -> Set[str]:
    """Extract unique species names from the records."""
    return {r['species_name'] for r in records if 'species_name' in r}

def verify_checksum() -> bool:
    """Verify the checksum of the existing file against the stored one."""
    if not OUTPUT_FILE.exists():
        return False
    if not CHECKSUM_FILE.exists():
        return False

    current_checksum = compute_checksum(OUTPUT_FILE)
    with open(CHECKSUM_FILE, 'r', encoding='utf-8') as f:
        stored_data = json.load(f)
    
    stored_checksum = stored_data.get('migratory_list.json')
    
    if current_checksum == stored_checksum:
        logger.info("Checksum verification passed. Using cached data.")
        return True
    else:
        logger.warning("Checksum mismatch. Re-downloading data.")
        return False

def update_checksum(file_name: str, checksum: str) -> None:
    """Update the checksum file with the new hash."""
    PROVENANCE_DIR.mkdir(parents=True, exist_ok=True)
    checksum_data = {}
    if CHECKSUM_FILE.exists():
        with open(CHECKSUM_FILE, 'r', encoding='utf-8') as f:
            checksum_data = json.load(f)
    
    checksum_data[file_name] = checksum
    
    with open(CHECKSUM_FILE, 'w', encoding='utf-8') as f:
        json.dump(checksum_data, f, indent=2)
    logger.info(f"Updated checksum for {file_name}")

def run_fetch_species_pipeline() -> Set[str]:
    """
    Main pipeline function for T015a.
    1. Check if file exists and checksum is valid.
    2. If valid, load and return species set.
    3. If not, download, save, compute checksum, update checksum file, and return species set.
    """
    # Ensure directories exist
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROVENANCE_DIR.mkdir(parents=True, exist_ok=True)

    # Check for existing valid data
    if verify_checksum():
        # Load from cache
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            records = json.load(f)
        return extract_migratory_species(records)

    # Download fresh data
    logger.info("Starting fresh download of migratory species list.")
    records = download_migratory_list()
    
    # Save to disk
    save_migratory_list(records, OUTPUT_FILE)
    
    # Compute and store checksum
    checksum = compute_checksum(OUTPUT_FILE)
    update_checksum("migratory_list.json", checksum)
    
    return extract_migratory_species(records)

def main():
    """Entry point for the script."""
    try:
        species_set = run_fetch_species_pipeline()
        logger.info(f"Pipeline completed. Retrieved {len(species_set)} unique migratory species.")
        # Print first few for verification (optional)
        # print(f"Sample species: {list(species_set)[:5]}")
        return species_set
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
