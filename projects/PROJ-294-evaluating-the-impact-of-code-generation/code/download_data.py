"""
Download HumanEval dataset from HuggingFace.

Downloads the full HumanEval dataset and saves it to data/raw/humaneval.parquet.
Computes SHA256 checksum for verification.

Output: data/raw/humaneval.parquet
"""
import os
import sys
import hashlib
import json
import time
import logging
from typing import Optional

# Import utilities from utils
try:
    from utils import setup_logging, get_logger, set_task_id, get_task_id, compute_sha256, ensure_directory
except ImportError:
    # Fallback for direct execution
    def setup_logging(task_id=None):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        return logging.getLogger(__name__)
    
    def get_logger(name):
        return logging.getLogger(name)
    
    def set_task_id(tid):
        pass
    
    def get_task_id():
        return None
    
    def compute_sha256(file_path):
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def ensure_directory(dir_path):
        os.makedirs(dir_path, exist_ok=True)
        return dir_path

TASK_ID = "T010"
DATASET_NAME = "openai/openai_humaneval"
OUTPUT_PATH = "data/raw/humaneval.parquet"
MAX_RETRIES = 3
RETRY_DELAY = 5

def get_file_path():
    """Get the output file path."""
    return OUTPUT_PATH

def verify_file_integrity(file_path: str, expected_checksum: Optional[str] = None) -> bool:
    """
    Verify file integrity using SHA256.
    
    Args:
        file_path: Path to the file
        expected_checksum: Optional expected checksum
        
    Returns:
        True if file exists and checksum matches (if provided)
    """
    if not os.path.exists(file_path):
        return False
    
    actual_checksum = compute_sha256(file_path)
    logging.info(f"Computed SHA256 for {file_path}: {actual_checksum}")
    
    if expected_checksum:
        return actual_checksum == expected_checksum
    return True

def download_humaneval():
    """
    Download the HumanEval dataset from HuggingFace.
    
    Uses streaming to handle large datasets efficiently.
    Saves to data/raw/humaneval.parquet.
    
    Raises:
        RuntimeError: If download fails after max retries
    """
    from datasets import load_dataset
    
    logging.info(f"Starting download of {DATASET_NAME}")
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Load dataset with streaming to handle large size
            logging.info(f"Attempt {attempt}/{MAX_RETRIES}")
            
            ds = load_dataset(DATASET_NAME, split="test", streaming=True)
            
            # Convert to list to ensure we have all data
            # For HumanEval (164 tasks), this is manageable in memory
            records = list(ds)
            
            logging.info(f"Downloaded {len(records)} records")
            
            if len(records) == 0:
                raise RuntimeError("Downloaded dataset is empty")
            
            # Save to parquet
            output_dir = os.path.dirname(OUTPUT_PATH)
            ensure_directory(output_dir)
            
            logging.info(f"Saving to {OUTPUT_PATH}")
            # Use pandas to save as parquet
            try:
                import pandas as pd
                df = pd.DataFrame(records)
                df.to_parquet(OUTPUT_PATH, index=False)
            except ImportError:
                # Fallback to JSON if pandas not available
                logging.warning("pandas not available, saving as JSON instead")
                json_path = OUTPUT_PATH.replace(".parquet", ".json")
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(records, f, indent=2, ensure_ascii=False)
                # Update path for checksum
                return json_path
            
            # Verify integrity
            if verify_file_integrity(OUTPUT_PATH):
                checksum = compute_sha256(OUTPUT_PATH)
                logging.info(f"Download complete. SHA256: {checksum}")
                return OUTPUT_PATH
            else:
                raise RuntimeError("Checksum verification failed")
                
        except Exception as e:
            logging.error(f"Download attempt {attempt} failed: {e}")
            if attempt < MAX_RETRIES:
                logging.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                raise RuntimeError(f"Failed to download verified real source after {MAX_RETRIES} attempts")
    
    raise RuntimeError("Failed to download verified real source")

def calculate_quartile_boundaries(data: list) -> dict:
    """
    Calculate quartile boundaries for a list of values.
    
    Args:
        data: List of numeric values
        
    Returns:
        Dictionary with Q1, Q2, Q3
    """
    if not data:
        return {"Q1": 0, "Q2": 0, "Q3": 0}
    
    sorted_data = sorted(data)
    n = len(sorted_data)
    
    Q2 = sorted_data[n // 2]
    Q1 = sorted_data[n // 4]
    Q3 = sorted_data[3 * n // 4]
    
    return {"Q1": Q1, "Q2": Q2, "Q3": Q3}

def main():
    """Main entry point for data download."""
    logger = setup_logging(task_id=TASK_ID)
    set_task_id(TASK_ID)
    
    logging.info(f"Starting HumanEval download (Task: {TASK_ID})")
    
    try:
        output_path = download_humaneval()
        logging.info(f"Data download successful: {output_path}")
        
        # Compute and log checksum
        checksum = compute_sha256(output_path)
        logging.info(f"Final checksum: {checksum}")
        
    except Exception as e:
        logging.error(f"Data download failed: {e}")
        sys.exit(1)
    
    logging.info(f"HumanEval download completed successfully (Task: {TASK_ID})")

if __name__ == "__main__":
    main()
