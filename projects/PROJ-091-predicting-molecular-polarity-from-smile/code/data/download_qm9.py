import os
import sys
import hashlib
import logging
import gzip
from pathlib import Path
from typing import Iterator, Tuple, List

from datasets import load_dataset
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Output paths relative to project root
DATA_RAW_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "raw"
OUTPUT_CSV = DATA_RAW_DIR / "qm9_smiles.csv"

def ensure_data_dir():
    """Ensure the data/raw directory exists."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_RAW_DIR

def compute_file_sha256(filepath: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_smiles_string(smiles: str) -> bool:
    """Basic validation of a SMILES string."""
    if not smiles or not isinstance(smiles, str):
        return False
    # Very basic check: non-empty, no spaces, allowed characters
    allowed = set("CcnnOoSsFClBrIP")
    # Simplified check; real validation would use RDKit
    return all(c in allowed or c in "[]()1234567890=" for c in smiles)

def stream_qm9_data() -> Iterator[Tuple[str, float]]:
    """
    Stream QM9 data from the verified HuggingFace source.
    Yields (smiles, target) tuples.
    Uses streaming=True to avoid OOM on large datasets.
    """
    # Verified source from execution feedback
    dataset_dict = load_dataset('jablonkagroup/qm9', 'raw_data', streaming=True)
    
    # Iterate over all splits (train, val, test)
    for split_name, split_data in dataset_dict.items():
        logger.info(f"Processing split: {split_name}")
        for row in split_data:
            smiles = row.get('SMILES')
            target = row.get('dipole_moment')
            
            if smiles and target is not None:
                # Basic validation before yielding
                if validate_smiles_string(smiles):
                    yield smiles, float(target)
                else:
                    logger.warning(f"Invalid SMILES skipped: {smiles[:20]}...")

def download_and_save_qm9():
    """
    Main entry point for QM9 download and saving to CSV.
    Streams data to avoid memory overflow and writes to data/raw/qm9_smiles.csv.
    """
    ensure_data_dir()
    
    if OUTPUT_CSV.exists():
        logger.info(f"{OUTPUT_CSV.name} already exists. Skipping download.")
        # Still validate existing file
        validate_smiles_file(OUTPUT_CSV)
        return

    logger.info("Starting QM9 download via streaming...")
    
    try:
        with open(OUTPUT_CSV, 'w', encoding='utf-8') as f:
            f.write("smiles,target\n")  # Header
            
            count = 0
            # Stream data
            for smiles, target in stream_qm9_data():
                # Write row
                f.write(f"{smiles},{target}\n")
                count += 1
                
                # Progress logging
                if count % 10000 == 0:
                    logger.info(f"Processed {count} records...")
                    
                    # Memory safety check (though streaming should prevent this)
                    # We don't store all data, but we monitor the buffer if we were
                    if sys.getsizeof(f) > 500 * 1024 * 1024:  # 500MB check
                        logger.warning("Output file size approaching limit, but streaming continues...")
            
            logger.info(f"Download complete. Total records: {count}")
            logger.info(f"Saved to {OUTPUT_CSV}")
            
    except Exception as e:
        logger.error(f"Failed to download/save QM9 data: {e}")
        # Clean up partial file
        if OUTPUT_CSV.exists():
            OUTPUT_CSV.unlink()
        raise

def validate_smiles_file(filepath: Path) -> int:
    """Validate SMILES in a file, return count of valid lines."""
    valid_count = 0
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # Skip header
            next(f, None)
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 2:
                    smiles = parts[0]
                    if validate_smiles_string(smiles):
                        valid_count += 1
    except Exception as e:
        logger.error(f"Error validating {filepath}: {e}")
        raise
    logger.info(f"Validated {valid_count} SMILES strings in {filepath.name}")
    return valid_count

def main():
    """Main entry point for QM9 download."""
    download_and_save_qm9()
    validate_smiles_file(OUTPUT_CSV)
    logger.info("QM9 data preparation complete.")

if __name__ == "__main__":
    main()
