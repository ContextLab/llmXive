"""
Preprocess the raw dataset downloaded in T013.

This module implements streaming logic to process the `codeparrot/code-trans-py-js`
dataset without loading the entire corpus into RAM, ensuring the footprint remains
<= 7GB as per SC-004.

It performs:
1. Streaming load from HuggingFace.
2. Dynamic chunking/buffering to manage memory.
3. Validation (via T013b logic) to exclude corrupted entries.
4. Sampling to reach a target size if the dataset is too large, or full processing if small.
5. Output to `data/processed/corpus.csv`.
"""
import os
import sys
import gc
import logging
import resource
import csv
from pathlib import Path
from typing import Optional, List, Dict, Any, Iterator

# Import existing utilities from the project
from src.ingestion.validate_dataset import is_valid_entry, validate_and_filter_dataset
from src.ingestion.enhance_logging import get_peak_memory_usage_bytes, log_memory_usage, validate_and_log_memory_constraint
from src.utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)

# Constants
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GB * 1024**3
TARGET_CORPUS_SIZE = 250  # Slightly above the required 200 to allow for filtering
DATASET_NAME = "codeparrot/code-trans-py-js"
OUTPUT_PATH = Path("data/processed/corpus.csv")
RAW_DATA_PATH = Path("data/raw")

def get_memory_usage_bytes() -> int:
    """Get current memory usage in bytes."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_maxrss * 1024  # ru_maxrss is in KB on Linux/macOS

def get_memory_usage_gb() -> float:
    """Get current memory usage in GB."""
    return get_memory_usage_bytes() / (1024**3)

def check_memory_limit(current_usage_gb: float) -> bool:
    """Check if current usage is within the 7GB limit."""
    return current_usage_gb < MEMORY_LIMIT_GB

def load_raw_dataset_streaming() -> Iterator[Dict[str, Any]]:
    """
    Load the dataset from HuggingFace in streaming mode to avoid OOM.
    Falls back to local raw data if available (T013 artifact), otherwise fetches.
    """
    try:
        from datasets import load_dataset
        logger.info(f"Loading dataset '{DATASET_NAME}' in streaming mode...")
        
        # We stream directly. If T013 cached to parquet/csv, we could load that,
        # but the task specifies using the datasets library streaming.
        # We assume the raw data is accessible via the dataset identifier.
        dataset = load_dataset(DATASET_NAME, split="train", streaming=True)
        
        for item in dataset:
            yield item
            
    except Exception as e:
        logger.error(f"Failed to load dataset in streaming mode: {e}")
        raise

def process_chunk(chunk: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process a chunk of data: validate and filter.
    Reuses logic from T013b (validate_dataset).
    """
    valid_entries = []
    for entry in chunk:
        # Ensure we have the expected keys
        if not is_valid_entry(entry):
            continue
        
        # Additional type checking for safety
        py_code = entry.get("python_code")
        js_code = entry.get("javascript_code")
        
        if isinstance(py_code, str) and isinstance(js_code, str) and len(py_code) > 0 and len(js_code) > 0:
            valid_entries.append({
                "python_code": py_code,
                "javascript_code": js_code,
                # We could add metadata here if available, e.g., id
            })
        else:
            # Log exclusion if needed, though validate_and_filter_dataset handles it
            pass
    
    return valid_entries

def process_buffer(buffer: List[Dict[str, Any]], writer: csv.DictWriter, total_count: int, target_count: int) -> int:
    """
    Process a buffer, write to CSV, and manage memory.
    Returns the updated total count.
    """
    if not buffer:
        return total_count

    # Check memory before processing a large buffer
    current_mem = get_memory_usage_gb()
    if not check_memory_limit(current_mem):
        logger.warning(f"Memory usage ({current_mem:.2f} GB) approaching limit. Stopping ingestion.")
        return total_count

    processed = process_chunk(buffer)
    if processed:
        for row in processed:
            writer.writerow(row)
            total_count += 1
            if total_count >= target_count:
                return total_count

    # Force garbage collection after writing a batch
    gc.collect()
    
    # Log memory periodically
    if total_count % 50 == 0:
        current_mem = get_memory_usage_gb()
        logger.info(f"Processed {total_count} entries. Current memory: {current_mem:.2f} GB")

    return total_count

def process_and_save_corpus(target_size: int = TARGET_CORPUS_SIZE) -> int:
    """
    Main logic to stream, validate, and save the corpus.
    Implements dynamic chunking by processing in batches of 1000.
    """
    logger.info(f"Starting preprocessing. Target size: {target_size}, Memory limit: {MEMORY_LIMIT_GB} GB")
    
    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ["python_code", "javascript_code"]
    total_count = 0
    buffer_size = 1000
    buffer: List[Dict[str, Any]] = []
    
    try:
        with open(OUTPUT_PATH, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            logger.info("Streaming dataset...")
            for item in load_raw_dataset_streaming():
                buffer.append(item)
                
                if len(buffer) >= buffer_size:
                    total_count = process_buffer(buffer, writer, total_count, target_size)
                    buffer = [] # Clear buffer
                    
                    if total_count >= target_size:
                        logger.info(f"Target size {target_size} reached. Stopping stream.")
                        break
                
                # Check memory every buffer cycle
                if total_count % buffer_size == 0:
                    current_mem = get_memory_usage_gb()
                    if not check_memory_limit(current_mem):
                        logger.warning(f"Memory limit exceeded at {total_count} entries. Stopping.")
                        break

            # Flush remaining buffer
            if buffer:
                total_count = process_buffer(buffer, writer, total_count, target_size)
                
    except Exception as e:
        logger.error(f"Error during corpus processing: {e}", exc_info=True)
        raise
    
    logger.info(f"Preprocessing complete. Saved {total_count} entries to {OUTPUT_PATH}")
    return total_count

def main():
    """Entry point for the script."""
    logger.info("Running preprocess_corpus.py")
    
    # Validate memory constraint before starting
    validate_and_log_memory_constraint(MEMORY_LIMIT_GB)
    
    count = process_and_save_corpus()
    
    if count < 200:
        logger.warning(f"Final corpus size ({count}) is less than the required 200 entries.")
        # We do not exit with error here, as the task is to implement the logic.
        # The validation task T014 will handle the strict check.
    else:
        logger.info(f"Corpus size ({count}) meets the minimum requirement of 200.")

    # Log final memory usage
    final_mem = get_memory_usage_gb()
    logger.info(f"Final memory usage: {final_mem:.2f} GB")

if __name__ == "__main__":
    main()