import os
import sys
import time
import logging
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path

# Import project-specific modules
from config import Config, get_secret
from utils.logging import get_logger, DataFetchError
from models.entities import FunctionSample

# Dataset library
try:
    from datasets import load_dataset
except ImportError:
    raise ImportError(
        "The 'datasets' package is required. Install it via: pip install datasets"
    )

# Constants
MAX_ATTEMPTS = 400
TARGET_VALID_FUNCTIONS = 200
MIN_VALID_FUNCTIONS = 100
DATASET_NAME = "bigcode/the-stack-dedup"
DATASET_SUBSET = "python"
DATA_DIR = "data/raw"
OUTPUT_FILE = "processed/raw_metrics.json" # Placeholder path, actual saving handled by processor

# Initialize logger
logger = get_logger(__name__)

def compute_hash(code: str) -> str:
    """Compute SHA-256 hash of the code string."""
    return hashlib.sha256(code.encode('utf-8')).hexdigest()

def is_valid_python_function(code: str) -> bool:
    """
    Check if the code string is a valid Python function.
    Attempts to parse the code using AST.
    """
    if not code or not isinstance(code, str):
        return False
    try:
        # Try to parse as a full module first
        ast.parse(code)
        # Additional check: ensure it's not just a snippet but contains definitions or valid statements
        # For this task, simple parse success is often enough, but we can be stricter if needed.
        # We'll rely on AST parsing success as the primary validator.
        return True
    except SyntaxError:
        return False
    except Exception:
        return False

def fetch_dataset_sample() -> Optional[str]:
    """
    Fetch a single Python function sample from the BigCode dataset.
    Uses streaming to avoid loading the entire dataset into memory.
    """
    try:
        # Load dataset in streaming mode
        dataset = load_dataset(
            DATASET_NAME,
            DATASET_SUBSET,
            split="train",
            streaming=True
        )
        
        # Iterate to get a random sample (streaming yields in order, so we take the next one)
        # In a real scenario, we might want to shuffle, but streaming shuffle is expensive.
        # We'll just take the next available item from the iterator.
        for item in dataset:
            # The dataset structure varies, but typically 'content' or 'code' holds the source
            # For the-stack-dedup, the field is usually 'content'
            code = item.get('content') or item.get('code')
            
            if code and isinstance(code, str) and len(code.strip()) > 0:
                return code
            
        return None
    except Exception as e:
        logger.error(f"Failed to fetch dataset sample: {e}")
        raise DataFetchError(f"Dataset access failed: {e}")

def download_valid_functions(
    max_attempts: int = MAX_ATTEMPTS,
    target_count: int = TARGET_VALID_FUNCTIONS,
    min_count: int = MIN_VALID_FUNCTIONS
) -> List[Dict[str, Any]]:
    """
    Fetch valid Python functions from the dataset.
    
    Args:
        max_attempts: Maximum number of fetch attempts.
        target_count: Target number of valid functions to collect.
        min_count: Minimum number of valid functions required to proceed.
        
    Returns:
        List of dictionaries containing 'code' and 'hash'.
        
    Raises:
        DataFetchError: If fewer than min_count valid functions are found.
    """
    valid_samples = []
    attempts = 0
    backoff = 1.0
    max_backoff = 60.0

    logger.info(f"Starting data fetch: max_attempts={max_attempts}, target={target_count}, min={min_count}")

    while attempts < max_attempts and len(valid_samples) < target_count:
        attempts += 1
        logger.debug(f"Attempt {attempts}/{max_attempts} (current valid: {len(valid_samples)})")

        try:
            code = fetch_dataset_sample()
            
            if code is None:
                logger.warning("Received None from dataset stream, retrying...")
                time.sleep(backoff)
                backoff = min(backoff * 2, max_backoff)
                continue

            if is_valid_python_function(code):
                sample_hash = compute_hash(code)
                valid_samples.append({
                    "code": code,
                    "hash": sample_hash
                })
                logger.debug(f"Valid function found. Total valid: {len(valid_samples)}")
                # Reset backoff on success
                backoff = 1.0
            else:
                logger.debug("Invalid Python syntax, skipping.")

        except DataFetchError as e:
            logger.error(f"Data fetch error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during fetch: {e}")
            # Exponential backoff for unexpected errors too
            time.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)
            continue

    logger.info(f"Fetch complete. Attempts: {attempts}, Valid samples: {len(valid_samples)}")

    if len(valid_samples) < min_count:
        error_msg = f"Insufficient valid functions found: {len(valid_samples)} < {min_count}. Pipeline halted."
        logger.error(error_msg)
        raise DataFetchError(error_msg)
    
    if min_count <= len(valid_samples) < target_count:
        logger.warning(
            f"Found {len(valid_samples)} valid functions, which is less than the target {target_count}. "
            f"Proceeding with available data as per Spec US-1 Scenario 4."
        )

    return valid_samples

def main():
    """Main entry point for the download script."""
    # Ensure output directory exists
    output_path = Path(DATA_DIR)
    output_path.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting data download process...")
    
    try:
        samples = download_valid_functions()
        
        # Save raw samples to a temporary JSON file for the next stage (processor)
        # Note: The actual processing and final saving is done in processor.py
        # We save here to satisfy the requirement of producing a file.
        output_file = output_path / "raw_samples.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(samples, f, indent=2)
            
        logger.info(f"Successfully saved {len(samples)} samples to {output_file}")
        print(f"Download complete: {len(samples)} valid functions saved.")
        
    except DataFetchError as e:
        logger.critical(f"Pipeline failed due to data fetch error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Pipeline failed with unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Import json here to avoid top-level dependency issues if not needed
    import json
    main()
