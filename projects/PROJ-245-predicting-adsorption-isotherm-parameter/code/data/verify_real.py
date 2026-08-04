"""
Verify Real Data Loader and Generate/Compare Reference Hash.

This script performs two functions depending on the mode:
1. Generate (T061a): Computes a checksum of the first 100 rows of the streamed
   NIST/MOF-1000 dataset and writes it to data/validation/reference_hash.json.
2. Verify (T061b): Compares the current data hash against the reference hash
   in data/validation/reference_hash.json. If they mismatch, it raises a
   DataIntegrityError.

Dependencies:
    - datasets (streaming)
    - pandas
    - hashlib
"""

import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from datasets import load_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATASET_ID = "nasa/nist-adsorption-isotherms"
SPLIT_NAME = "train"
SAMPLE_SIZE = 100
OUTPUT_DIR = Path("data/validation")
REFERENCE_FILE = OUTPUT_DIR / "reference_hash.json"
CURRENT_HASH_FILE = OUTPUT_DIR / "current_hash.json"


class DataIntegrityError(Exception):
    """Raised when data integrity verification fails."""
    pass


def compute_row_hash(row: Dict[str, Any]) -> str:
    """
    Compute a SHA-256 hash for a single row based on its stringified content.
    
    Args:
        row: A dictionary representing a dataset row.
            
    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    # Sort keys to ensure consistent hashing regardless of dict order
    sorted_items = sorted(row.items())
    # Convert to a canonical string representation
    canonical_str = json.dumps(sorted_items, sort_keys=True, default=str)
    return hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()


def generate_reference_hash() -> Dict[str, Any]:
    """
    Stream the first N rows from the real dataset, compute a cumulative hash,
    and return the result metadata.
    
    Returns:
        Dictionary containing the hash, sample size, dataset ID, and timestamp.
        
    Raises:
      ConnectionError: If the dataset cannot be fetched.
      ValueError: If the dataset ID is invalid or empty.
    """
    logger.info(f"Attempting to stream dataset: {DATASET_ID}")
    
    try:
        # Load dataset in streaming mode
        dataset = load_dataset(
            DATASET_ID, 
            split=SPLIT_NAME, 
            streaming=True,
            trust_remote_code=True
        )
    except Exception as e:
        logger.error(f"Failed to load dataset {DATASET_ID}: {e}")
        raise ConnectionError(f"Real data fetch failed: {e}")

    # Collect first N rows
    rows = []
    try:
        for i, row in enumerate(dataset):
            if i >= SAMPLE_SIZE:
                break
            rows.append(row)
    except Exception as e:
        logger.error(f"Failed to iterate over dataset rows: {e}")
        raise ConnectionError(f"Data iteration failed: {e}")

    if not rows:
        raise ValueError("Dataset is empty or could not be read.")

    logger.info(f"Successfully retrieved {len(rows)} rows for hashing.")

    # Compute cumulative hash
    # We hash the concatenation of individual row hashes to ensure order matters
    # and to handle large datasets if we ever increased the sample size.
    cumulative_hash_input = ""
    for row in rows:
        row_hash = compute_row_hash(row)
        cumulative_hash_input += row_hash

    final_hash = hashlib.sha256(cumulative_hash_input.encode('utf-8')).hexdigest()

    result = {
        "dataset_id": DATASET_ID,
        "split": SPLIT_NAME,
        "sample_size": len(rows),
        "reference_hash": final_hash,
        "algorithm": "SHA-256",
        "description": "Cumulative hash of the first 100 rows of the streamed NIST/MOF-1000 dataset.",
        "timestamp": None  # Will be set by the caller or main
    }

    return result


def verify_against_reference() -> bool:
    """
    Stream the first N rows from the real dataset, compute the current hash,
    and compare it against the reference hash stored in data/validation/reference_hash.json.
    
    Returns:
        True if hashes match.
        
    Raises:
        DataIntegrityError: If the reference file is missing or hashes do not match.
        ConnectionError: If the dataset cannot be fetched to compute the current hash.
    """
    logger.info("Starting verification against reference hash.")

    # 1. Check if reference file exists
    if not REFERENCE_FILE.exists():
        raise DataIntegrityError(f"Reference hash file not found: {REFERENCE_FILE}. "
                                 "Run with mode='generate' first to create it.")

    # 2. Load reference hash
    try:
        with open(REFERENCE_FILE, 'r') as f:
            reference_data = json.load(f)
        expected_hash = reference_data.get("reference_hash")
        if not expected_hash:
            raise DataIntegrityError("Reference hash file exists but 'reference_hash' key is missing.")
    except json.JSONDecodeError as e:
        raise DataIntegrityError(f"Failed to parse reference hash file: {e}")
    
    logger.info(f"Loaded expected hash from {REFERENCE_FILE}: {expected_hash[:16]}...")

    # 3. Compute current hash from real data
    logger.info(f"Fetching current data from {DATASET_ID} to compute hash...")
    
    try:
        dataset = load_dataset(
            DATASET_ID, 
            split=SPLIT_NAME, 
            streaming=True,
            trust_remote_code=True
        )
    except Exception as e:
        logger.error(f"Failed to load dataset {DATASET_ID}: {e}")
        raise ConnectionError(f"Real data fetch failed for verification: {e}")

    rows = []
    try:
        for i, row in enumerate(dataset):
            if i >= SAMPLE_SIZE:
                break
            rows.append(row)
    except Exception as e:
        logger.error(f"Failed to iterate over dataset rows: {e}")
        raise ConnectionError(f"Data iteration failed during verification: {e}")

    if not rows:
        raise ValueError("Dataset is empty or could not be read during verification.")

    logger.info(f"Successfully retrieved {len(rows)} rows for current hash computation.")

    cumulative_hash_input = ""
    for row in rows:
        row_hash = compute_row_hash(row)
        cumulative_hash_input += row_hash

    current_hash = hashlib.sha256(cumulative_hash_input.encode('utf-8')).hexdigest()
    
    logger.info(f"Computed current hash: {current_hash[:16]}...")

    # 4. Compare
    if current_hash != expected_hash:
        error_msg = (
            f"Data Integrity Error: Hash mismatch detected.\n"
            f"Expected: {expected_hash}\n"
            f"Current:  {current_hash}\n"
            f"The data source may have changed or been corrupted."
        )
        logger.error(error_msg)
        raise DataIntegrityError(error_msg)

    logger.info("Verification successful: Current data matches reference hash.")
    
    # Optional: Write current hash for audit trail
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    audit_result = {
        "dataset_id": DATASET_ID,
        "split": SPLIT_NAME,
        "sample_size": len(rows),
        "current_hash": current_hash,
        "match": True,
        "algorithm": "SHA-256",
        "timestamp": None
    }
    from datetime import datetime
    audit_result["timestamp"] = datetime.utcnow().isoformat()
    
    with open(CURRENT_HASH_FILE, 'w') as f:
        json.dump(audit_result, f, indent=2)
    
    return True


def main():
    """
    Main entry point for the verification script.
    Supports two modes via CLI arguments:
      --mode generate: Creates the reference hash (T061a).
      --mode verify:   Compares current data against reference (T061b).
    Default is 'verify' if the reference exists, otherwise 'generate'.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Verify or Generate Real Data Hash")
    parser.add_argument("--mode", choices=["generate", "verify"], default=None,
                        help="Mode: 'generate' to create reference, 'verify' to check integrity.")
    args = parser.parse_args()

    mode = args.mode

    # Auto-detect mode if not specified
    if mode is None:
        if REFERENCE_FILE.exists():
            mode = "verify"
        else:
            mode = "generate"
    
    logger.info(f"Running in mode: {mode}")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        if mode == "generate":
            logger.info("Starting reference hash generation for T061a.")
            result = generate_reference_hash()
            from datetime import datetime
            result["timestamp"] = datetime.utcnow().isoformat()

            with open(REFERENCE_FILE, 'w') as f:
                json.dump(result, f, indent=2)

            logger.info(f"Reference hash successfully written to {REFERENCE_FILE}")
            logger.info(f"Hash Value: {result['reference_hash']}")
            
        elif mode == "verify":
            logger.info("Starting verification against reference hash for T061b.")
            verify_against_reference()
            logger.info("Data integrity verified successfully.")
        
        return 0

    except DataIntegrityError as e:
        logger.error(f"Data Integrity Error: {e}")
        return 1
    except ConnectionError as e:
        logger.error(f"Connection Error: {e}")
        return 2
    except Exception as e:
        logger.error(f"Critical failure: {e}")
        raise


if __name__ == "__main__":
    sys.exit(main())