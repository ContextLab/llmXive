import os
import sys
import gzip
import json
import hashlib
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Local imports matching API surface
from utils.logging import get_logger
from utils.config import get_data_dir

logger = get_logger(__name__)

# Constants
FAILURE_THRESHOLD_RATE = 0.10  # 10%
ZINC15_URL_TEMPLATE = "https://zinc15.docking.org/subsets/filtered/{}.smiles.gz"
# Using a specific small subset for demonstration if not specified, 
# but the logic holds for any valid subset ID. 
# In a real run, this should be passed via CLI or config.
DEFAULT_SUBSET_ID = "drug-like" 

def validate_smiles(smiles: str) -> bool:
    """
    Validates a SMILES string using RDKit.
    
    Args:
        smiles: The SMILES string to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    try:
        from rdkit import Chem
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return False
        # Basic sanity check: molecule must have at least one atom
        if mol.GetNumAtoms() == 0:
            return False
        return True
    except Exception as e:
        logger.debug(f"RDKit validation error for SMILES '{smiles[:20]}...': {e}")
        return False

def fetch_zinc15_data(subset_id: str = DEFAULT_SUBSET_ID, output_dir: Optional[Path] = None) -> Path:
    """
    Fetches ZINC15 data from the specified subset URL.
    
    Args:
        subset_id: The ZINC15 subset identifier (e.g., 'drug-like').
        output_dir: Directory to save the downloaded file. Defaults to data/raw.
        
    Returns:
        Path to the downloaded file.
        
    Raises:
        RuntimeError: If the download fails.
    """
    import urllib.request
    import urllib.error

    if output_dir is None:
        output_dir = get_data_dir() / "raw"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"zinc15_{subset_id}.smiles.gz"
    file_path = output_dir / filename
    url = ZINC15_URL_TEMPLATE.format(subset_id)

    if file_path.exists():
        logger.info(f"Data file already exists: {file_path}")
        return file_path

    logger.info(f"Fetching ZINC15 data from {url}...")
    try:
        urllib.request.urlretrieve(url, file_path)
        logger.info(f"Successfully downloaded {file_path}")
    except urllib.error.URLError as e:
        logger.error(f"Failed to download ZINC15 data: {e}")
        raise RuntimeError(f"Failed to fetch ZINC15 data: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        raise RuntimeError(f"Unexpected error during download: {e}")
    
    return file_path

def process_smiles_file(file_path: Path) -> Tuple[List[str], int, int]:
    """
    Processes a SMILES file, validates each entry, and returns valid SMILES.
    
    Args:
        file_path: Path to the .smiles.gz file.
        
    Returns:
        Tuple of (list of valid SMILES, total count, failure count).
        
    Raises:
        RuntimeError: If failure rate exceeds 10%.
    """
    valid_smiles = []
    total_count = 0
    failure_count = 0

    logger.info(f"Processing SMILES file: {file_path}")

    try:
        with gzip.open(file_path, 'rt', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                total_count += 1
                smiles = line.split()[0] if line.split() else "" # Handle potential whitespace
                
                if not smiles:
                    failure_count += 1
                    continue

                if validate_smiles(smiles):
                    valid_smiles.append(smiles)
                else:
                    failure_count += 1
                    
                # Progress logging
                if total_count % 10000 == 0:
                    logger.info(f"Processed {total_count} lines, {len(valid_smiles)} valid, {failure_count} invalid.")

    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise

    failure_rate = failure_count / total_count if total_count > 0 else 0.0
    
    logger.info(f"Processing complete. Total: {total_count}, Valid: {len(valid_smiles)}, Invalid: {failure_count}")
    logger.info(f"Failure rate: {failure_rate:.2%}")

    if failure_rate > FAILURE_THRESHOLD_RATE:
        error_msg = f"CRITICAL: SMILES validation failure rate ({failure_rate:.2%}) exceeds threshold ({FAILURE_THRESHOLD_RATE:.2%}). Halting pipeline."
        logger.critical(error_msg)
        raise RuntimeError(error_msg)

    return valid_smiles, total_count, failure_count

def calculate_checksums(file_path: Path) -> str:
    """
    Calculates the SHA256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hex digest of the checksum.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    """
    Main entry point for the ingestion pipeline with validation and error handling.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Ingest and validate ZINC15 SMILES data.")
    parser.add_argument("--subset", type=str, default=DEFAULT_SUBSET_ID, help="ZINC15 subset ID")
    parser.add_argument("--output", type=str, default=None, help="Output directory for processed data")
    args = parser.parse_args()

    # Setup paths
    output_dir = Path(args.output) if args.output else get_data_dir() / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Fetch Data
        data_file = fetch_zinc15_data(subset_id=args.subset, output_dir=output_dir)
        
        # 2. Validate and Process
        valid_smiles, total, failures = process_smiles_file(data_file)
        
        # 3. Save Valid Data
        output_file = output_dir / f"valid_{args.subset}_smiles.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            for smiles in valid_smiles:
                f.write(f"{smiles}\n")
        
        logger.info(f"Saved {len(valid_smiles)} valid SMILES to {output_file}")
        
        # 4. Checksum
        checksum = calculate_checksums(data_file)
        checksum_file = output_dir / f"{args.subset}.sha256"
        with open(checksum_file, 'w') as f:
            f.write(checksum)
        
        logger.info(f"Checksum saved to {checksum_file}")
        
    except RuntimeError as e:
        # Re-raise critical errors (like >10% failure) to halt the pipeline
        logger.critical(f"Pipeline halted: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
