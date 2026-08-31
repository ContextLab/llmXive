import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataIntegrityError(Exception):
    """Raised when data verification against reference fails."""
    pass

def compute_row_hash(row: pd.Series) -> str:
    """
    Compute a hash for a single row based on all its values.
    We sort the items to ensure consistent hashing regardless of column order.
    """
    # Convert row to a string representation of sorted items
    # We handle NaNs by converting them to a specific string representation
    items = []
    for col in sorted(row.index):
        val = row[col]
        if pd.isna(val):
            items.append(f"{col}:NaN")
        else:
            items.append(f"{col}:{str(val)}")
    
    row_str = "|".join(items)
    return hashlib.sha256(row_str.encode('utf-8')).hexdigest()

def generate_reference_hash(data_path: str, output_path: str, sample_size: int = 100) -> None:
    """
    Generate a reference hash from the first N rows of the dataset.
    Writes the result to output_path.
    
    Args:
        data_path: Path to the input data file (parquet or csv)
        output_path: Path to write the reference_hash.json
        sample_size: Number of rows to sample for the hash
    """
    logger.info(f"Generating reference hash from {data_path} (sample size: {sample_size})")
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    # Load data based on extension
    if data_path.endswith('.parquet'):
        df = pd.read_parquet(data_path)
    elif data_path.endswith('.csv'):
        df = pd.read_csv(data_path)
    else:
        # Try parquet first, fallback to csv
        try:
            df = pd.read_parquet(data_path)
        except Exception:
            df = pd.read_csv(data_path)
    
    # Take the first N rows
    sample_df = df.head(sample_size)
    
    # Compute hash for each row and combine them
    row_hashes = [compute_row_hash(row) for _, row in sample_df.iterrows()]
    combined_hash_str = "|".join(row_hashes)
    final_hash = hashlib.sha256(combined_hash_str.encode('utf-8')).hexdigest()
    
    # Create reference object
    reference_data = {
        "sample_size": sample_size,
        "data_file": os.path.basename(data_path),
        "hash": final_hash,
        "row_hashes": row_hashes,
        "generated_at": pd.Timestamp.now().isoformat()
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Write to file
    with open(output_path, 'w') as f:
        json.dump(reference_data, f, indent=2)
    
    logger.info(f"Reference hash generated: {final_hash}")
    logger.info(f"Reference hash written to {output_path}")

def verify_against_reference(data_path: str, reference_path: str) -> bool:
    """
    Verify current data against a stored reference hash.
    
    Args:
        data_path: Path to the current data file to verify
        reference_path: Path to the reference_hash.json file
        
    Returns:
        True if verification passes
        
    Raises:
        DataIntegrityError: If hash mismatch or file not found
    """
    logger.info(f"Verifying data at {data_path} against reference at {reference_path}")
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found for verification: {data_path}")
    
    if not os.path.exists(reference_path):
        raise FileNotFoundError(f"Reference hash file not found: {reference_path}")
    
    # Load reference hash
    with open(reference_path, 'r') as f:
        reference_data = json.load(f)
    
    expected_hash = reference_data['hash']
    expected_sample_size = reference_data.get('sample_size', 100)
    
    # Load current data
    if data_path.endswith('.parquet'):
        df = pd.read_parquet(data_path)
    elif data_path.endswith('.csv'):
        df = pd.read_csv(data_path)
    else:
        try:
            df = pd.read_parquet(data_path)
        except Exception:
            df = pd.read_csv(data_path)
    
    # Check sample size
    if len(df) < expected_sample_size:
        logger.warning(f"Current dataset has {len(df)} rows, expected at least {expected_sample_size}")
    
    # Compute current hash
    sample_df = df.head(expected_sample_size)
    row_hashes = [compute_row_hash(row) for _, row in sample_df.iterrows()]
    combined_hash_str = "|".join(row_hashes)
    current_hash = hashlib.sha256(combined_hash_str.encode('utf-8')).hexdigest()
    
    logger.info(f"Expected hash: {expected_hash}")
    logger.info(f"Current hash:  {current_hash}")
    
    if current_hash != expected_hash:
        error_msg = (
            f"Data integrity check FAILED! Hash mismatch.\n"
            f"Expected: {expected_hash}\n"
            f"Current:  {current_hash}\n"
            f"Data source may have changed or been corrupted."
        )
        logger.error(error_msg)
        raise DataIntegrityError(error_msg)
    
    logger.info("Data integrity check PASSED.")
    return True

def main():
    """
    Main entry point for the verification script.
    Can be used to generate a reference hash or verify against one.
    
    Usage:
        # Generate reference hash
        python code/data/verify_real.py --mode generate --data data/raw/streamed_chunk_0.parquet --output data/validation/reference_hash.json
        
        # Verify against reference
        python code/data/verify_real.py --mode verify --data data/raw/streamed_chunk_0.parquet --reference data/validation/reference_hash.json
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify real data integrity against reference hash")
    parser.add_argument('--mode', choices=['generate', 'verify'], required=True,
                      help='Mode: generate reference hash or verify against reference')
    parser.add_argument('--data', required=True, help='Path to the data file')
    parser.add_argument('--output', help='Path for output reference hash (required for generate mode)')
    parser.add_argument('--reference', help='Path to reference hash file (required for verify mode)')
    parser.add_argument('--sample-size', type=int, default=100, help='Number of rows to sample for hashing')
    
    args = parser.parse_args()
    
    try:
        if args.mode == 'generate':
            if not args.output:
                parser.error("--output is required for generate mode")
            generate_reference_hash(args.data, args.output, args.sample_size)
            print(f"Reference hash generated successfully at {args.output}")
            
        elif args.mode == 'verify':
            if not args.reference:
                parser.error("--reference is required for verify mode")
            verify_against_reference(args.data, args.reference)
            print("Data verification successful.")
            
    except DataIntegrityError as e:
        print(f"VERIFICATION FAILED: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"FILE NOT FOUND: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error during verification")
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()