"""
Data Download Module for Molecular Complexity Analysis.
Handles fetching molecules from the HuggingFace dataset with streaming,
retry logic, and checksum verification.
"""
import hashlib
import json
import os
import sys
import time
import logging
from typing import Iterator, Dict, Any, Optional
from pathlib import Path

# Import config to get dataset ID and retry settings
# Note: We import specific names to avoid circular imports if config imports this
try:
    from config import DATASET_ID, MAX_RETRIES, SEED
except ImportError:
    # Fallback for standalone execution or if config is not fully ready
    DATASET_ID = "sagawa/pubchem-10m-canonicalized"
    MAX_RETRIES = 3
    SEED = 42

# Import datasets
try:
    from datasets import load_dataset
except ImportError:
    raise ImportError("The 'datasets' package is required. Install via: pip install datasets")

logger = logging.getLogger(__name__)

def compute_file_checksum(file_path: str, algorithm: str = "sha256") -> str:
    """
    Computes the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).
    
    Returns:
        Hexadecimal string of the checksum.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """
    Verifies the checksum of a file against an expected value.
    
    Args:
        file_path: Path to the file.
        expected_checksum: Expected SHA-256 hex string.
    
    Returns:
        True if checksum matches, False otherwise.
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found for checksum verification: {file_path}")
        return False
    
    actual_checksum = compute_file_checksum(file_path)
    if actual_checksum.lower() != expected_checksum.lower():
        logger.error(f"Checksum mismatch for {file_path}. Expected: {expected_checksum}, Got: {actual_checksum}")
        return False
    
    logger.info(f"Checksum verified for {file_path}")
    return True

def fetch_molecules() -> Iterator[Dict[str, Any]]:
    """
    Fetches molecules from the HuggingFace dataset using streaming.
    Implements exponential backoff retry logic for network errors.
    
    Yields:
        Dict with 'cid' (int) and 'smiles' (str).
    
    Raises:
        Exception: If data fetch fails after MAX_RETRIES attempts.
    """
    logger.info(f"Initializing dataset fetch from: {DATASET_ID}")
    
    attempt = 0
    last_error = None
    
    while attempt < MAX_RETRIES:
        try:
            # Load dataset in streaming mode to handle large sizes
            # The dataset 'sagawa/pubchem-10m-canonicalized' typically has 'cid' and 'smiles' columns
            ds = load_dataset(DATASET_ID, split="train", streaming=True)
            
            logger.info("Dataset loaded successfully in streaming mode.")
            
            for item in ds:
                # Validate and normalize the data structure
                if 'cid' not in item or 'smiles' not in item:
                    logger.warning(f"Skipping item missing required fields: {item.keys()}")
                    continue
                
                # Ensure types are correct
                cid = int(item['cid'])
                smiles = str(item['smiles'])
                
                # Basic validation: SMILES should not be empty
                if not smiles or smiles.strip() == "":
                    continue
                    
                yield {'cid': cid, 'smiles': smiles}
            
            # If we reach here, the stream completed successfully
            return

        except Exception as e:
            last_error = e
            attempt += 1
            wait_time = (2 ** attempt) + 1  # Exponential backoff
            logger.warning(f"Attempt {attempt}/{MAX_RETRIES} failed: {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)
    
    # If we reach here, all retries failed
    logger.error(f"Failed to fetch molecules after {MAX_RETRIES} attempts.")
    raise last_error

def load_and_sample_dataset(sample_size: Optional[int] = None) -> Iterator[Dict[str, Any]]:
    """
    Wrapper to fetch molecules, optionally limiting to a sample size.
    
    Args:
        sample_size: Maximum number of molecules to yield. If None, yields all.
    
    Yields:
        Dict with 'cid' and 'smiles'.
    """
    count = 0
    for molecule in fetch_molecules():
        yield molecule
        count += 1
        if sample_size and count >= sample_size:
            logger.info(f"Reached sample limit of {sample_size}. Stopping stream.")
            break

def main():
    """
    Main entry point for testing the download functionality.
    Runs a small sample fetch to verify connectivity and data structure.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    logger.info("Starting download module test.")
    
    try:
        # Fetch a small sample to verify
        count = 0
        for mol in load_and_sample_dataset(sample_size=5):
            logger.info(f"Retrieved: CID={mol['cid']}, SMILES={mol['smiles'][:20]}...")
            count += 1
        
        logger.info(f"Successfully fetched {count} molecules.")
        
    except Exception as e:
        logger.error(f"Download failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()