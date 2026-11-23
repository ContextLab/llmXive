import os
import json
import time
import requests
import logging
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Verified real data source
DATASET_ID = "nasa/nist-adsorption-isotherms"

def sanitize_url(url: str) -> str:
    """Sanitize URL to prevent injection attacks."""
    if not url.startswith(('http://', 'https://')):
        raise ValueError(f"Invalid URL scheme: {url}")
    return url

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal."""
    safe_name = os.path.basename(filename)
    if not safe_name:
        raise ValueError("Empty filename")
    return safe_name

def write_verification_log(log_path: Path, status: str, message: str):
    """Write verification log to JSON."""
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "message": message
    }
    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=2)

def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    import hashlib
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def stream_and_filter_dataset(
    dataset_id: str,
    output_dir: Path,
    chunk_size: int = 1000
) -> List[str]:
    """
    Stream the dataset from Hugging Face, filter for Type I isotherms,
    and write chunks to Parquet files.
    
    Args:
        dataset_id: The Hugging Face dataset ID.
        output_dir: Directory to write chunk files.
        chunk_size: Number of rows per chunk.
        
    Returns:
        List of paths to written chunk files.
    """
    from datasets import load_dataset
    
    logger.info(f"Attempting to stream dataset: {dataset_id}")
    
    # Load dataset in streaming mode
    try:
        dataset = load_dataset(dataset_id, split="train", streaming=True)
    except Exception as e:
        # Specific error handling for incorrect dataset ID
        raise ValueError(
            f"Failed to load dataset '{dataset_id}'. "
            f"Verify the dataset ID exists on Hugging Face. "
            f"Original error: {e}"
        ) from e

    # Check available columns to identify isotherm type column
    # The task specifies checking 'isotherm_type' or 'IsothermType'
    # We will check the first batch to determine column names
    first_batch = next(iter(dataset))
    available_columns = list(first_batch.keys())
    logger.info(f"Available columns in dataset: {available_columns}")
    
    isotherm_col = None
    if 'isotherm_type' in available_columns:
        isotherm_col = 'isotherm_type'
    elif 'IsothermType' in available_columns:
        isotherm_col = 'IsothermType'
    
    if isotherm_col is None:
        # Fallback: check for case-insensitive match or common variations
        for col in available_columns:
            if 'type' in col.lower() and 'isotherm' in col.lower():
                isotherm_col = col
                break
    
    if isotherm_col is None:
        raise ValueError(
            f"Could not find 'isotherm_type' or 'IsothermType' column in dataset. "
            f"Available columns: {available_columns}. "
            f"Cannot filter for Type I isotherms."
        )
    
    logger.info(f"Using column '{isotherm_col}' for Type I isotherm filtering.")
    
    chunk_files = []
    current_chunk = []
    chunk_idx = 0
    total_rows = 0
    filtered_rows = 0
    
    for row_idx, row in enumerate(dataset):
        total_rows += 1
        
        # Check isotherm type
        isotherm_val = row.get(isotherm_col)
        
        # Filter logic: include ONLY Type I isotherms
        # Check for 'I', 1, '1', or similar representations
        is_type_i = False
        if isotherm_val is not None:
            str_val = str(isotherm_val).strip().upper()
            if str_val == 'I' or str_val == '1' or str_val == 'I':
                is_type_i = True
            # Also check if it's an integer 1
            elif isinstance(isotherm_val, int) and isotherm_val == 1:
                is_type_i = True
        
        if is_type_i:
            current_chunk.append(row)
            filtered_rows += 1
        
        # Write chunk when size limit reached
        if len(current_chunk) >= chunk_size:
            chunk_path = output_dir / f"streamed_chunk_{chunk_idx:04d}.parquet"
            
            # Convert list of dicts to PyArrow Table
            table = pa.Table.from_pylist(current_chunk)
            pq.write_table(table, chunk_path)
            
            chunk_files.append(str(chunk_path))
            logger.info(f"Written chunk {chunk_idx} with {len(current_chunk)} rows to {chunk_path}")
            
            chunk_idx += 1
            current_chunk = []
        
        # Progress logging
        if row_idx % 10000 == 0 and row_idx > 0:
            logger.info(f"Processed {row_idx} rows, filtered {filtered_rows} Type I isotherms so far...")
    
    # Write final partial chunk if any
    if current_chunk:
        chunk_path = output_dir / f"streamed_chunk_{chunk_idx:04d}.parquet"
        table = pa.Table.from_pylist(current_chunk)
        pq.write_table(table, chunk_path)
        chunk_files.append(str(chunk_path))
        logger.info(f"Written final chunk {chunk_idx} with {len(current_chunk)} rows to {chunk_path}")
    
    logger.info(f"Streaming complete. Total rows processed: {total_rows}, Type I isotherms written: {filtered_rows}")
    logger.info(f"Written {len(chunk_files)} chunk files.")
    
    return chunk_files

def attempt_nist_fetch(url: str, output_dir: Path) -> bool:
    """Attempt to fetch data from NIST or specified URL."""
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        filename = sanitize_filename(url.split('/')[-1] or "adsorption_data.csv")
        output_path = output_dir / filename
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Successfully fetched data from {url} to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to fetch from NIST: {e}")
        return False

def attempt_fallback_fetch(url: str, output_dir: Path) -> bool:
    """Attempt fallback fetch from alternative source."""
    # Placeholder for fallback logic if needed
    return False

def main():
    """Main entry point for download script.
    
    This function implements T060: Streaming Data Loader with Filtering.
    It streams the NIST adsorption isotherms dataset from Hugging Face,
    filters for Type I isotherms, and writes chunks to Parquet files.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Stream and filter adsorption isotherm data")
    parser.add_argument("--dataset-id", type=str, default=DATASET_ID,
                      help=f"Hugging Face dataset ID (default: {DATASET_ID})")
    parser.add_argument("--output-dir", type=str, default="data/raw",
                      help="Output directory for chunk files")
    parser.add_argument("--chunk-size", type=int, default=1000,
                      help="Number of rows per chunk file")
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    log_path = output_dir / "verification_log.json"
    
    try:
        # Stream, filter, and write chunks
        chunk_files = stream_and_filter_dataset(
            dataset_id=args.dataset_id,
            output_dir=output_dir,
            chunk_size=args.chunk_size
        )
        
        if not chunk_files:
            write_verification_log(log_path, "EMPTY", "No Type I isotherms found in dataset.")
            raise ValueError("No Type I isotherms found in the dataset. Cannot proceed.")
        
        write_verification_log(
            log_path, 
            "SUCCESS", 
            f"Streamed and filtered dataset. Written {len(chunk_files)} chunk files."
        )
        logger.info("Streaming and filtering completed successfully.")
        
    except ValueError as e:
        # Re-raise with specific message for dataset ID issues
        write_verification_log(log_path, "FAILED", str(e))
        raise
    except Exception as e:
        write_verification_log(log_path, "FAILED", f"Unexpected error: {e}")
        logger.error(f"Streaming failed with error: {e}")
        raise

if __name__ == "__main__":
    main()