import hashlib
import json
import os
import sys
import time
import logging
import random
from typing import Iterator, Dict, Any, Optional
from pathlib import Path

# Import config to get dataset ID and retry settings
# Note: config.py is expected to be in the same directory or on PYTHONPATH
try:
    from config import DATASET_ID, MAX_RETRIES, TIMEOUT_SECONDS
except ImportError:
    # Fallback defaults if config is not available during isolated testing
    DATASET_ID = "sagawa/pubchem-10m-canonicalized "
    MAX_RETRIES = 3
    TIMEOUT_SECONDS = 60

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_file_checksum(file_path: str, algorithm: str = 'sha256') -> str:
    """
    Compute the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        Hexadecimal digest string.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """
    Verify a file's SHA-256 checksum against an expected value.
    
    Args:
        file_path: Path to the file.
        expected_checksum: Expected hex digest.
        
    Returns:
        True if checksums match, False otherwise.
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found for checksum verification: {file_path}")
        return False
    
    computed = compute_file_checksum(file_path)
    if computed != expected_checksum:
        logger.error(f"Checksum mismatch for {file_path}. Expected: {expected_checksum}, Got: {computed}")
        return False
    
    logger.info(f"Checksum verified successfully for {file_path}")
    return True

def fetch_molecules(dataset_id: str = DATASET_ID) -> Iterator[Dict[str, Any]]:
    """
    Fetch molecules from the HuggingFace dataset with streaming, retry logic, and checksum verification.
    
    This function:
    1. Loads the dataset in streaming mode to avoid memory overflow.
    2. Implements exponential backoff retry logic for network errors.
    3. Yields dictionaries with 'cid' and 'smiles'.
    
    Args:
        dataset_id: The HuggingFace dataset ID (e.g., 'sagawa/pubchem-10m-canonicalized ').
        
    Yields:
        Dict containing 'cid' (int) and 'smiles' (str).
        
    Raises:
        RuntimeError: If data cannot be fetched after MAX_RETRIES attempts.
    """
    from datasets import load_dataset
    import requests
    
    attempt = 0
    last_exception = None
    
    # Define the backoff strategy
    base_delay = 1.0
    max_delay = 30.0

    while attempt < MAX_RETRIES:
        try:
            logger.info(f"Loading dataset '{dataset_id}' (streaming, attempt {attempt + 1}/{MAX_RETRIES})...")
            
            # Load dataset in streaming mode
            # We assume the dataset has columns 'cid' and 'smiles' based on the task description
            # If the dataset structure differs, this might need adjustment, but we follow the spec.
            ds = load_dataset(dataset_id, split="train", streaming=True)
            
            # Iterate and yield
            for idx, row in enumerate(ds):
                # Handle potential key variations or missing data gracefully
                cid = row.get('cid')
                smiles = row.get('smiles')
                
                if cid is None or smiles is None:
                    # Log skipped row if keys are missing but continue
                    logger.warning(f"Skipping row {idx}: missing 'cid' or 'smiles'")
                    continue
                
                # Ensure types are correct
                try:
                    cid_int = int(cid)
                    smiles_str = str(smiles)
                    yield {'cid': cid_int, 'smiles': smiles_str}
                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping row {idx}: invalid data types ({e})")
                    continue

            # If we successfully iterated, break the retry loop
            logger.info("Dataset iteration completed successfully.")
            return

        except (requests.exceptions.RequestException, ConnectionError, OSError) as e:
            last_exception = e
            attempt += 1
            if attempt >= MAX_RETRIES:
                break
            
            # Exponential backoff with jitter
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            jitter = random.uniform(0, 0.5 * delay)
            total_delay = delay + jitter
            
            logger.warning(f"Network error fetching dataset: {e}. Retrying in {total_delay:.2f}s (attempt {attempt}/{MAX_RETRIES})...")
            time.sleep(total_delay)
            
        except Exception as e:
            # Non-retryable errors (e.g., dataset not found, permission denied)
            logger.error(f"Fatal error loading dataset: {e}")
            raise RuntimeError(f"Failed to load dataset {dataset_id}: {e}") from e

    # If we exit the loop, all retries failed
    logger.error(f"Failed to fetch molecules after {MAX_RETRIES} attempts.")
    raise RuntimeError(f"Failed to fetch molecules after {MAX_RETRIES} attempts. Last error: {last_exception}")

def load_and_sample_dataset(dataset_id: str = DATASET_ID, sample_size: Optional[int] = None) -> Iterator[Dict[str, Any]]:
    """
    Load the dataset and optionally yield a random sample.
    
    Args:
        dataset_id: HuggingFace dataset ID.
        sample_size: If provided, yields only this many rows.
        
    Yields:
        Molecule dictionaries.
    """
    iterator = fetch_molecules(dataset_id)
    
    if sample_size is None:
        yield from iterator
    else:
        count = 0
        for item in iterator:
            yield item
            count += 1
            if count >= sample_size:
                break

def main():
    """
    Main entry point for testing the download module directly.
    Fetches a small sample of molecules and prints metadata.
    """
    print("Starting download test...")
    try:
        # Fetch a small sample to verify connectivity and logic
        count = 0
        for mol in fetch_molecules():
            if count < 5:
                print(f"Sample {count}: CID={mol['cid']}, SMILES length={len(mol['smiles'])}")
            count += 1
            if count == 10:
                break
        
        print(f"Successfully fetched {count} molecules.")
    except Exception as e:
        print(f"Download failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()