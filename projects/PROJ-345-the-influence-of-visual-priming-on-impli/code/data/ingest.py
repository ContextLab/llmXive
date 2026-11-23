import os
import csv
import hashlib
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Iterator, Any, Generator

import pandas as pd
import requests

from code.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants for chunking
CHUNK_SIZE = 10000  # Rows per chunk for processing
MEMORY_LIMIT_GB = 6.0  # Conservative limit to stay under 7GB

class IngestConfig:
    """Configuration for data ingestion."""
    def __init__(self, source_url: str, output_dir: str):
        self.source_url = source_url
        self.output_dir = Path(output_dir)
        self.chunk_size = CHUNK_SIZE

def calculate_checksum(file_path: Path) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def download_file_from_osf(url: str, dest_path: Path, chunk_size: int = 8192) -> bool:
    """
    Download a file from OSF/HF with progress tracking.
    Returns True if successful, False otherwise.
    """
    try:
        logger.info(f"Downloading from {url} to {dest_path}")
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        if downloaded % (total_size // 100 + 1) == 0:
                            logger.info(f"Download progress: {progress:.1f}%")
        
        logger.info("Download completed successfully")
        return True
    except requests.RequestException as e:
        logger.error(f"Failed to download file: {e}")
        return False

def load_iat_csv_chunked(file_path: Path, chunk_size: int = CHUNK_SIZE) -> Generator[pd.DataFrame, None, None]:
    """
    Generator that yields chunks of a CSV file to handle large datasets efficiently.
    This prevents loading the entire file into memory at once.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Use pandas chunking for efficient memory usage
    chunker = pd.read_csv(file_path, chunksize=chunk_size)
    for chunk in chunker:
        yield chunk

def extract_trial_data_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    """
    Extract and validate trial-level data from a chunk.
    Ensures necessary columns exist and filters invalid rows.
    """
    required_cols = ['trial_id', 'response_time', 'stimulus_id', 'prime_condition', 'participant_id']
    
    # Check for required columns
    missing_cols = [col for col in required_cols if col not in chunk.columns]
    if missing_cols:
        logger.warning(f"Chunk missing columns: {missing_cols}. Dropping chunk.")
        return pd.DataFrame()
    
    # Filter out rows with invalid response times (e.g., negative or zero)
    valid_chunk = chunk[
        (chunk['response_time'] > 0) & 
        (chunk['response_time'] < 20000)  # Reasonable upper bound for RT
    ].copy()
    
    return valid_chunk

def validate_trial_data(df: pd.DataFrame) -> Tuple[int, int]:
    """
    Validate trial data and return (total_rows, valid_rows).
    """
    total = len(df)
    if total == 0:
        return 0, 0
    
    valid = df[
        (df['response_time'] > 0) & 
        (df['response_time'] < 20000) &
        (df['trial_id'].notna()) &
        (df['participant_id'].notna())
    ].shape[0]
    
    return total, valid

def check_missing_images(trials_df: pd.DataFrame, primes_dir: Path, targets_dir: Path) -> Tuple[float, List[str]]:
    """
    Check for missing image files referenced in the trial data.
    Returns (missing_percentage, list_of_missing_stimuli).
    """
    missing_count = 0
    missing_stimuli = []
    
    all_stimuli = trials_df['stimulus_id'].unique()
    
    for stim_id in all_stimuli:
        # Determine if prime or target based on naming convention or metadata
        # Assuming stimulus_id contains type info or we check both dirs
        prime_path = primes_dir / f"{stim_id}.png"
        target_path = targets_dir / f"{stim_id}.png"
        
        if not prime_path.exists() and not target_path.exists():
            missing_count += 1
            missing_stimuli.append(stim_id)
    
    total_stimuli = len(all_stimuli)
    missing_pct = (missing_count / total_stimuli * 100) if total_stimuli > 0 else 0.0
    
    return missing_pct, missing_stimuli

def ingest_iat_data_chunked(config: IngestConfig) -> bool:
    """
    Main ingestion pipeline with chunked processing for large datasets.
    Handles datasets >7GB by processing in chunks and aggregating results.
    """
    raw_dir = Config.DATA_RAW
    processed_dir = Config.DATA_PROCESSED
    
    # Ensure directories exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    local_file = raw_dir / "iat_data.csv"
    
    # Download data
    if not download_file_from_osf(config.source_url, local_file):
        logger.error("Data download failed. Aborting ingestion.")
        return False
    
    # Verify checksum
    checksum = calculate_checksum(local_file)
    logger.info(f"Downloaded file checksum: {checksum}")
    
    # Process in chunks
    logger.info("Starting chunked processing...")
    processed_chunks = []
    total_rows = 0
    valid_rows = 0
    
    try:
        for i, chunk in enumerate(load_iat_csv_chunked(local_file, config.chunk_size)):
            logger.info(f"Processing chunk {i+1}")
            
            # Extract and validate
            valid_chunk = extract_trial_data_chunk(chunk)
            total, valid = validate_trial_data(valid_chunk)
            
            total_rows += total
            valid_rows += valid
            
            if not valid_chunk.empty:
                processed_chunks.append(valid_chunk)
            
            # Explicit garbage collection to free memory
            if (i + 1) % 5 == 0:
                logger.info("Running garbage collection...")
                import gc
                gc.collect()
        
        if not processed_chunks:
            logger.error("No valid data found in any chunk.")
            return False
        
        # Concatenate chunks
        logger.info("Concatenating processed chunks...")
        full_df = pd.concat(processed_chunks, ignore_index=True)
        
        # Check for missing images
        primes_dir = Config.PRIMES
        targets_dir = Config.TARGETS
        missing_pct, missing_list = check_missing_images(full_df, primes_dir, targets_dir)
        
        logger.info(f"Missing image percentage: {missing_pct:.2f}%")
        
        if missing_pct > 10.0:
            logger.error(f"Data Gap: Image files missing for >10% of trials ({missing_pct:.2f}%). Halting.")
            return False
        elif missing_pct > 0:
            logger.warning(f"Warning: {missing_pct:.2f}% images missing. Excluding missing trials.")
            # Filter out missing stimuli
            valid_stimuli = set(primes_dir.glob("*.png")) | set(targets_dir.glob("*.png"))
            valid_stimuli_ids = {p.stem for p in valid_stimuli}
            full_df = full_df[full_df['stimulus_id'].isin(valid_stimuli_ids)]
        
        # Write final output
        output_path = processed_dir / "linked_trials.csv"
        full_df.to_csv(output_path, index=False)
        logger.info(f"Successfully wrote {len(full_df)} trials to {output_path}")
        
        return True
        
    except MemoryError:
        logger.error("Memory error during processing. Consider reducing chunk_size.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during ingestion: {e}")
        return False

def main():
    """Entry point for ingestion script."""
    # Example usage - in real scenario, URL would be from config or CLI
    config = IngestConfig(
        source_url="https://osf.io/download/example_iat_dataset", 
        output_dir=str(Config.DATA_PROCESSED)
    )
    
    success = ingest_iat_data_chunked(config)
    if success:
        logger.info("Ingestion completed successfully.")
        sys.exit(0)
    else:
        logger.error("Ingestion failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()