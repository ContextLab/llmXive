import sys
import os
import hashlib
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from datasets import load_dataset

# Import project utilities
from src.utils.logging import get_ingestion_logger
from src.utils.data_provenance import generate_provenance_header
from src.utils.config import get_project_root

logger = get_ingestion_logger(__name__)

# Configuration
DATASET_ID = "taqwa92/cm.mgb2"
OUTPUT_DIR = "data/raw"
OUTPUT_FILE = "supercon_mgb2.csv"
CACHE_CHECKSUM_FILE = "data/raw/.supercon_checksum.txt"
PROVENANCE_HEADER_FILE = "data/raw/.supercon_provenance.txt"
IMPURITY_THRESHOLD = 0.50  # Fail if >50% entries lack impurity columns

def calculate_file_checksum(filepath: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_impurity_coverage(df: pd.DataFrame) -> bool:
    """
    Check if more than 50% of entries lack impurity columns.
    Returns True if valid (<=50% missing), False if invalid (>50% missing).
    """
    # Define expected impurity columns (common in SuperCon for MgB2)
    # We look for columns that typically represent impurities in MgB2
    possible_impurity_cols = [col for col in df.columns if 'impurity' in col.lower() or 'dopant' in col.lower()]
    
    if not possible_impurity_cols:
        # If no impurity columns exist at all, that's 100% missing
        logger.warning("No impurity columns found in dataset")
        return False

    # Check for rows where ALL impurity columns are null/empty
    impurity_mask = df[possible_impurity_cols].isna().all(axis=1)
    missing_ratio = impurity_mask.sum() / len(df)
    
    logger.info(f"Impurity column check: {missing_ratio:.2%} of entries lack impurity data")
    
    if missing_ratio > IMPURITY_THRESHOLD:
        logger.error(f"Too many entries ({missing_ratio:.2%}) lack impurity data. Threshold: {IMPURITY_THRESHOLD:.2%}")
        return False
    
    return True

def has_impurity_columns(df: pd.DataFrame) -> bool:
    """Check if the dataframe has any impurity-related columns."""
    possible_impurity_cols = [col for col in df.columns if 'impurity' in col.lower() or 'dopant' in col.lower()]
    return len(possible_impurity_cols) > 0

def load_supercon_dataset() -> pd.DataFrame:
    """
    Load the SuperCon MgB2 dataset from HuggingFace.
    Returns the dataframe if successful.
    """
    logger.info(f"Loading dataset {DATASET_ID} from HuggingFace...")
    try:
        dataset = load_dataset(DATASET_ID, split="train")
        df = dataset.to_pandas()
        logger.info(f"Successfully loaded {len(df)} entries from {DATASET_ID}")
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset {DATASET_ID}: {e}")
        raise

def attach_provenance_header(filepath: str, source: str):
    """Attach provenance header to the CSV file."""
    timestamp = datetime.utcnow().isoformat()
    version = "1.0.0"
    header = generate_provenance_header(source=source, timestamp=timestamp, version=version)
    
    # Read existing content
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Prepend header
    final_content = header + "\n" + content
    
    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    logger.info(f"Attached provenance header to {filepath}")

def main():
    """Main entry point for downloading and validating SuperCon dataset."""
    project_root = get_project_root()
    output_path = project_root / OUTPUT_DIR / OUTPUT_FILE
    cache_checksum_path = project_root / CACHE_CHECKSUM_FILE
    provenance_path = project_root / PROVENANCE_HEADER_FILE

    # Ensure output directory exists
    output_dir = project_root / OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check if cached file exists
    if output_path.exists():
        logger.info(f"Found cached file: {output_path}")
        
        # Verify checksum
        if cache_checksum_path.exists():
            with open(cache_checksum_path, 'r') as f:
                cached_checksum = f.read().strip()
            
            current_checksum = calculate_file_checksum(str(output_path))
            
            if current_checksum == cached_checksum:
                logger.info("Checksum matches. Validating provenance header...")
                # Verify provenance header exists
                if provenance_path.exists():
                    logger.info("Provenance header exists. Exiting early.")
                    return 0
                else:
                    # Missing provenance, but checksum valid - attach it and exit
                    logger.warning("Provenance header missing. Attaching now.")
                    attach_provenance_header(str(output_path), f"cached:{DATASET_ID}")
                    with open(provenance_path, 'w') as f:
                        f.write(f"provenance_attached:{datetime.utcnow().isoformat()}")
                    return 0
            else:
                logger.error("Checksum mismatch. Aborting to prevent corruption.")
                sys.exit(1)
        else:
            logger.warning("Checksum file missing. Re-fetching dataset.")
    else:
        logger.info("No cached file found. Fetching from HuggingFace.")

    # Fetch dataset
    try:
        df = load_supercon_dataset()
    except Exception as e:
        logger.error(f"Failed to fetch dataset: {e}")
        sys.exit(1)

    # Validate impurity coverage
    if not validate_impurity_coverage(df):
        logger.error("Dataset validation failed: >50% of entries lack impurity columns.")
        sys.exit(1)

    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Saved dataset to {output_path}")

    # Calculate and save checksum
    checksum = calculate_file_checksum(str(output_path))
    with open(cache_checksum_path, 'w') as f:
        f.write(checksum)
    logger.info(f"Saved checksum: {checksum}")

    # Attach provenance header
    attach_provenance_header(str(output_path), f"hf:{DATASET_ID}")
    with open(provenance_path, 'w') as f:
        f.write(f"provenance_attached:{datetime.utcnow().isoformat()}")

    logger.info("SuperCon dataset download and validation completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
