"""
MolNet Data Download Script for PROJ-413.

This script downloads molecular interaction data from the MolNet dataset via Hugging Face.
It validates the presence of required fields (polymer_smiles, filler_smiles, adhesion_energy)
and computes SHA256 checksums for state tracking.

If required fields are missing, it triggers a hard abort (E-DATA-001).
"""
import os
import sys
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from datasets import load_dataset
from utils.exceptions import DataError
from utils.logger import PerformanceLogger, get_memory_usage_mb
from utils.hash_state import compute_sha256
from utils.seed_utils import set_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / 'results' / 'download.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
DATASET_NAME = "molnet"
REQUIRED_FIELDS = ["polymer_smiles", "filler_smiles", "adhesion_energy"]
OUTPUT_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "molnet_raw.json"
CHECKSUM_FILE = OUTPUT_DIR / "molnet_checksums.json"
EXIT_CODE_DATA_001 = 100

def compute_file_sha256(filepath: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_molnet_data() -> List[Dict[str, Any]]:
    """
    Download MolNet dataset.
    
    Returns:
        List of records containing molecular data.
        
    Raises:
        DataError: If the dataset cannot be loaded or is empty.
    """
    logger.info(f"Loading dataset: {DATASET_NAME}...")
    try:
        # Attempt to load the dataset. 
        # Note: MolNet in HF datasets is often split by specific tasks.
        # We try to load the full collection or a relevant subset.
        # If 'molnet' doesn't exist directly as a single dataset, we might need to 
        # load specific subsets like 'esol' or 'freesolv' if they contain interaction data,
        # but the task specifies 'molnet'. We assume the plan's existence of such a dataset
        # or a wrapper that aggregates it.
        # Fallback: If 'molnet' is not a direct key, we try to load a common subset 
        # that might contain the required fields, or raise an error if the specific
        # dataset structure is not found.
        
        # Attempting to load the generic 'molnet' dataset if available in the hub.
        # If the hub does not have a single 'molnet' dataset with these specific columns,
        # this will raise an exception, which we catch and handle.
        dataset = load_dataset(DATASET_NAME, split="train")
        
        # If the dataset loads but doesn't have the columns, we check below.
        # If it's a multi-split dataset, we might need to concatenate, but for now
        # we assume a flat structure or the first split.
        return dataset.to_list()
        
    except Exception as e:
        logger.error(f"Failed to load dataset '{DATASET_NAME}': {e}")
        # Check if it's a specific key error for missing dataset
        if "Couldn't find a dataset script" in str(e) or "Dataset not found" in str(e):
            raise DataError(f"Dataset '{DATASET_NAME}' not found in Hugging Face Hub. "
                            "Cannot proceed without real data source.") from e
        raise DataError(f"Error loading dataset: {e}") from e

def validate_fields(data: List[Dict[str, Any]]) -> bool:
    """
    Validate that all required fields are present in the data.
    
    Args:
        data: List of records.
        
    Returns:
        True if valid, raises DataError otherwise.
    """
    if not data:
        raise DataError("Dataset is empty. Cannot proceed.")

    # Check keys in the first record
    first_record = data[0]
    missing_fields = [field for field in REQUIRED_FIELDS if field not in first_record]
    
    if missing_fields:
        raise DataError(
            f"Missing required fields in dataset: {missing_fields}. "
            "Hard abort triggered (E-DATA-001). The Plan requires these fields for "
            "adhesion energy prediction. NIST cross-reference is not available as a fallback."
        )
    
    # Check for nulls in the required fields across a sample (or all if small)
    # For large datasets, we might sample, but let's check the schema first.
    null_count = {field: 0 for field in REQUIRED_FIELDS}
    sample_size = min(len(data), 1000)
    
    for record in data[:sample_size]:
        for field in REQUIRED_FIELDS:
            if record.get(field) is None or (isinstance(record.get(field), float) and str(record.get(field)) == 'nan'):
                null_count[field] += 1
    
    for field, count in null_count.items():
        if count > 0:
            pct = (count / sample_size) * 100
            logger.warning(f"Field '{field}' has {count} nulls in sample ({pct:.2f}%). "
                           "This may trigger validation logic in T013.")
    
    return True

def save_data(data: List[Dict[str, Any]], output_path: Path) -> str:
    """Save data to JSON and return checksum."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        
    checksum = compute_file_sha256(output_path)
    logger.info(f"Data saved to {output_path} (SHA256: {checksum})")
    return checksum

def save_checksums(checksums: Dict[str, str], checksum_path: Path) -> None:
    """Save checksums to a JSON file."""
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checksum_path, 'w', encoding='utf-8') as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Checksums saved to {checksum_path}")

def main():
    """Main entry point for the download script."""
    set_seed(42) # Ensure reproducibility for any random sampling if needed
    logger.info("Starting MolNet data download (T011)...")
    
    start_time = PerformanceLogger.start()
    
    try:
        # 1. Download
        raw_data = download_molnet_data()
        
        # 2. Validate
        validate_fields(raw_data)
        
        # 3. Save
        checksum = save_data(raw_data, OUTPUT_FILE)
        
        # 4. Record Checksums
        checksums = {
            "molnet_raw.json": checksum,
            "dataset_name": DATASET_NAME
        }
        save_checksums(checksums, CHECKSUM_FILE)
        
        end_time = PerformanceLogger.stop()
        mem_usage = get_memory_usage_mb()
        
        logger.info(f"Download completed successfully. Records: {len(raw_data)}, "
                    f"Memory: {mem_usage:.2f} MB, Time: {end_time - start_time:.2f}s")
        
        return 0
        
    except DataError as e:
        logger.critical(f"Data Error (E-DATA-001): {e}")
        # Print specific exit code to stderr for shell detection
        print(f"EXIT_CODE:{EXIT_CODE_DATA_001}", file=sys.stderr)
        return EXIT_CODE_DATA_001
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
