"""
T010: Download HumanEval dataset from HuggingFace.

Downloads the full HumanEval dataset (openai/openai_humaneval) using revision="main".
Saves raw data to data/raw/humaneval.parquet and computes SHA256 checksum.

Constraints:
- Must NOT fall back to synthetic data.
- Must raise RuntimeError with message "Failed to download verified real source" on failure.
- Must stream the real data if large (though HumanEval is small, we use the streaming pattern for consistency).
"""
import os
import sys
import json
import time
import logging
import hashlib
from typing import Optional, Dict, Any, List

# Import shared utilities from utils.py
# Note: utils.py is expected to exist in the same directory (code/)
try:
    from utils import setup_logging, get_logger, set_task_id, get_task_id, compute_sha256
except ImportError:
    # Fallback if utils is not importable (e.g., running directly)
    import logging
    import hashlib
    import uuid
    from datetime import datetime

    def setup_logging(task_id: Optional[str] = None) -> logging.Logger:
        logger = logging.getLogger(f"T010_{task_id or 'download'}")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] [%(name)s] - %(message)s'))
            logger.addHandler(handler)
        return logger

    def get_logger() -> logging.Logger:
        return logging.getLogger("T010")

    def set_task_id(tid: str) -> None:
        pass

    def get_task_id() -> str:
        return "T010"

    def compute_sha256(file_path: str) -> str:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

# Constants
DATASET_NAME = "openai/openai_humaneval"
REVISION = "main"
OUTPUT_DIR = "data/raw"
OUTPUT_FILE_NAME = "humaneval.parquet"
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

def ensure_output_dir() -> None:
    """Ensure the output directory exists."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR, exist_ok=True)

def download_humaneval(logger: logging.Logger) -> Optional[List[Dict[str, Any]]]:
    """
    Download the HumanEval dataset from HuggingFace Hub.
    
    Uses the `datasets` library to load the dataset and streams it to avoid memory issues.
    Returns the data as a list of dictionaries, or None if download fails.
    
    Raises:
        RuntimeError: If download fails after max retries.
    """
    logger.info(f"Attempting to download dataset: {DATASET_NAME} (revision={REVISION})")
    
    retries = 0
    last_exception = None

    while retries < MAX_RETRIES:
        try:
            # Import here to avoid dependency issues if datasets is not installed
            from datasets import load_dataset
            
            # Load the dataset with streaming to handle potential large sizes gracefully
            # Although HumanEval is small, this follows the "streaming" constraint.
            ds = load_dataset(DATASET_NAME, split="test", revision=REVISION, streaming=True)
            
            # Convert to list of dicts. Since HumanEval is small (~164 items),
            # we can safely materialize it.
            data = list(ds)
            
            if not data:
                logger.error("Downloaded dataset is empty.")
                raise RuntimeError("Downloaded dataset is empty.")
            
            logger.info(f"Successfully downloaded {len(data)} records.")
            logger.info(f"Fields: {data[0].keys()}")
            
            return data

        except Exception as e:
            last_exception = e
            retries += 1
            logger.warning(f"Download attempt {retries}/{MAX_RETRIES} failed: {e}")
            if retries < MAX_RETRIES:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"Failed to download verified real source after {MAX_RETRIES} retries.")
                raise RuntimeError("Failed to download verified real source") from e

    # Should not reach here, but just in case
    raise RuntimeError("Failed to download verified real source") from last_exception

def save_to_parquet(data: List[Dict[str, Any]], output_path: str, logger: logging.Logger) -> None:
    """
    Save the downloaded data to a Parquet file.
    
    Args:
        data: List of dictionaries containing the dataset records.
        output_path: Path to the output Parquet file.
        logger: Logger instance.
    """
    logger.info(f"Saving data to {output_path}")
    
    try:
        import pandas as pd
        df = pd.DataFrame(data)
        df.to_parquet(output_path, index=False)
        logger.info(f"Saved {len(df)} records to {output_path}")
    except ImportError:
        logger.error("pandas and pyarrow are required to save Parquet files. Install with: pip install pandas pyarrow")
        raise
    except Exception as e:
        logger.error(f"Failed to save Parquet file: {e}")
        raise

def save_to_jsonl(data: List[Dict[str, Any]], output_path: str, logger: logging.Logger) -> None:
    """
    Save the downloaded data to a JSONL file as a fallback or alternative format.
    
    Args:
        data: List of dictionaries containing the dataset records.
        output_path: Path to the output JSONL file.
        logger: Logger instance.
    """
    logger.info(f"Saving data to {output_path}")
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for record in data:
                f.write(json.dumps(record) + '\n')
        logger.info(f"Saved {len(data)} records to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save JSONL file: {e}")
        raise

def verify_file_integrity(file_path: str, logger: logging.Logger) -> str:
    """
    Compute and log the SHA256 checksum of the output file.
    
    Args:
        file_path: Path to the file.
        logger: Logger instance.
        
    Returns:
        The SHA256 checksum string.
    """
    checksum = compute_sha256(file_path)
    logger.info(f"SHA256 checksum of {file_path}: {checksum}")
    
    # Save checksum to a sidecar file
    checksum_path = file_path + ".sha256"
    with open(checksum_path, 'w') as f:
        f.write(checksum)
    logger.info(f"Saved checksum to {checksum_path}")
    
    return checksum

def main() -> None:
    """Main entry point for T010."""
    task_id = get_task_id() or "T010"
    logger = setup_logging(task_id=task_id)
    set_task_id(task_id)
    
    logger.info("Starting T010: Download HumanEval Dataset")
    
    try:
        # Ensure output directory exists
        ensure_output_dir()
        
        # Download data
        data = download_humaneval(logger)
        
        if data is None:
            logger.error("Download returned no data.")
            sys.exit(1)
        
        # Save to Parquet
        parquet_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE_NAME)
        save_to_parquet(data, parquet_path, logger)
        
        # Also save to JSONL for compatibility with other scripts that might expect it
        jsonl_path = os.path.join(OUTPUT_DIR, "humaneval_test.jsonl")
        save_to_jsonl(data, jsonl_path, logger)
        
        # Verify integrity
        verify_file_integrity(parquet_path, logger)
        
        logger.info("T010 completed successfully.")
        
    except RuntimeError as e:
        logger.error(f"Critical error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error in T010: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
