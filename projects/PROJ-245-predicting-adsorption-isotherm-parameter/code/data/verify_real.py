import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataIntegrityError(Exception):
    """Raised when data integrity verification fails."""
    pass

def ensure_directories():
    """Ensure required directories exist."""
    validation_dir = Path("data/validation")
    validation_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directory exists: {validation_dir}")

def compute_row_hash(row: Dict[str, Any]) -> str:
    """
    Compute a SHA256 hash for a single row of data.
    The hash is computed over a sorted tuple of (key, value) pairs to ensure consistency.
    """
    # Convert row to a sorted tuple of items to ensure consistent hashing
    # Handle unhashable types (like lists/dicts) by converting them to strings
    sortable_items = []
    for k, v in sorted(row.items()):
        if isinstance(v, (list, dict)):
            sortable_items.append((k, json.dumps(v, sort_keys=True)))
        else:
            sortable_items.append((k, str(v)))
    
    row_str = json.dumps(sortable_items, sort_keys=True)
    return hashlib.sha256(row_str.encode('utf-8')).hexdigest()

def compute_dataset_hash(rows: List[Dict[str, Any]], sample_size: int = 100) -> str:
    """
    Compute a dataset hash based on the first N rows (or all if fewer).
    This serves as a checksum for the dataset content.
    """
    if not rows:
        return hashlib.sha256(b"empty_dataset").hexdigest()
    
    # Take the first sample_size rows (or all if less)
    sample_rows = rows[:sample_size]
    
    # Compute hash for each row
    row_hashes = [compute_row_hash(row) for row in sample_rows]
    
    # Combine all row hashes into a single string
    combined_hash_str = "".join(row_hashes)
    
    # Compute final SHA256 hash
    final_hash = hashlib.sha256(combined_hash_str.encode('utf-8')).hexdigest()
    return final_hash

def load_dataset_chunk(data_path: str, sample_size: int = 100) -> List[Dict[str, Any]]:
    """
    Load a chunk of data from a parquet file.
    """
    try:
        import pandas as pd
        # Read the parquet file
        df = pd.read_parquet(data_path)
        
        # Convert to list of dictionaries
        rows = df.to_dict('records')
        
        logger.info(f"Loaded {len(rows)} rows from {data_path}")
        
        if len(rows) > sample_size:
            logger.info(f"Sampling first {sample_size} rows for hashing")
            return rows[:sample_size]
        
        return rows
    except Exception as e:
        logger.error(f"Failed to load dataset chunk from {data_path}: {e}")
        raise

def generate_reference_hash(data_path: str, output_path: str, sample_size: int = 100):
    """
    Generate a reference hash for the dataset and save it to a JSON file.
    This is used by T061a.
    """
    ensure_directories()
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    rows = load_dataset_chunk(data_path, sample_size)
    dataset_hash = compute_dataset_hash(rows, sample_size)
    
    reference_data = {
        "hash": dataset_hash,
        "sample_size": sample_size,
        "data_source": data_path,
        "generated_at": str(Path(data_path).stat().st_mtime),
        "description": "Reference hash for data integrity verification"
    }
    
    with open(output_path, 'w') as f:
        json.dump(reference_data, f, indent=2)
    
    logger.info(f"Reference hash generated and saved to {output_path}: {dataset_hash}")
    return dataset_hash

def verify_against_reference(data_path: str, reference_path: str, sample_size: int = 100):
    """
    Verify the current data hash against a stored reference hash.
    Raises DataIntegrityError if the hashes do not match.
    """
    ensure_directories()
    
    # Check if reference file exists
    if not os.path.exists(reference_path):
        raise FileNotFoundError(f"Reference hash file not found: {reference_path}")
    
    # Load reference hash
    with open(reference_path, 'r') as f:
        reference_data = json.load(f)
    
    expected_hash = reference_data.get("hash")
    if not expected_hash:
        raise ValueError("Reference hash file does not contain a 'hash' field")
    
    logger.info(f"Loaded reference hash: {expected_hash}")
    
    # Check if data file exists
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    # Compute current hash
    rows = load_dataset_chunk(data_path, sample_size)
    current_hash = compute_dataset_hash(rows, sample_size)
    
    logger.info(f"Computed current hash: {current_hash}")
    
    # Compare hashes
    if current_hash != expected_hash:
        error_msg = (
            f"Data integrity check FAILED!\n"
            f"Expected hash: {expected_hash}\n"
            f"Current hash:  {current_hash}\n"
            f"Data may have been modified or corrupted."
        )
        logger.error(error_msg)
        raise DataIntegrityError(error_msg)
    
    logger.info("Data integrity check PASSED. Hashes match.")
    return True

def main():
    """
    Main entry point for the verification script.
    Usage:
      python code/data/verify_real.py --data-path data/raw/merged_dataset.parquet --ref-path data/validation/reference_hash.json
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify data integrity against reference hash")
    parser.add_argument("--data-path", type=str, required=True, help="Path to the data file to verify")
    parser.add_argument("--ref-path", type=str, required=True, help="Path to the reference hash file")
    parser.add_argument("--sample-size", type=int, default=100, help="Number of rows to sample for hashing")
    
    args = parser.parse_args()
    
    try:
        verify_against_reference(args.data_path, args.ref_path, args.sample_size)
        print("Verification successful: Data integrity confirmed.")
        sys.exit(0)
    except DataIntegrityError as e:
        print(f"Verification failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()