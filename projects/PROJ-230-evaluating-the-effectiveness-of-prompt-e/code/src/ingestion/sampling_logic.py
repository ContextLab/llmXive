"""
T013c: Sampling and chunking logic for memory-constrained dataset processing.

Implements streaming/chunked loading of the raw dataset to ensure the processed
dataset footprint remains ≤7GB RAM. Outputs the final corpus to 
data/processed/corpus.csv.

Dependencies:
- datasets (from T013)
- pandas
- src.utils.logging (for structured logging)
- src.ingestion.enhance_logging (for memory tracking)
"""
import os
import gc
import logging
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Iterator
import pandas as pd
from datasets import load_dataset
from src.utils.logging import get_logger
from src.ingestion.enhance_logging import (
    get_peak_memory_usage_bytes,
    get_peak_memory_usage_gb,
    log_memory_usage,
    validate_and_log_memory_constraint
)

# Constants
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GB * 1024 ** 3
CHUNK_SIZE = 500  # Rows per chunk during processing
OUTPUT_PATH = "data/processed/corpus.csv"
RAW_DATA_PATH = "data/raw"

logger = get_logger(__name__)


def load_raw_dataset_streaming(dataset_name: str, split: str = "train") -> Iterator[Dict[str, Any]]:
    """
    Load the dataset in streaming mode to avoid loading the entire dataset into memory.
    
    Args:
        dataset_name: HuggingFace dataset identifier (e.g., 'codeparrot/code-trans-py-js')
        split: Dataset split to load (default: 'train')
        
    Returns:
        Iterator yielding one row (dict) at a time.
    """
    logger.info(f"Loading dataset '{dataset_name}' in streaming mode for split '{split}'...")
    try:
        dataset = load_dataset(dataset_name, split=split, streaming=True)
        logger.info(f"Dataset loaded successfully. Starting iteration.")
        return iter(dataset)
    except Exception as e:
        logger.error(f"Failed to load dataset '{dataset_name}': {e}")
        raise


def process_chunk(chunk_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Process a chunk of data, extracting relevant columns and filtering invalid entries.
    
    Args:
        chunk_data: List of dictionaries representing rows from the dataset.
        
    Returns:
        DataFrame containing valid entries with 'python_code' and 'javascript_code' columns.
    """
    if not chunk_data:
        return pd.DataFrame()
    
    df = pd.DataFrame(chunk_data)
    
    # Ensure required columns exist
    required_cols = ['python_code', 'javascript_code']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.warning(f"Missing required columns in chunk: {missing_cols}. Dropping chunk.")
        return pd.DataFrame()
    
    # Filter out rows with missing or non-string code
    valid_mask = (
        df['python_code'].notna() & 
        df['javascript_code'].notna() & 
        df['python_code'].apply(lambda x: isinstance(x, str) and len(x.strip()) > 0) &
        df['javascript_code'].apply(lambda x: isinstance(x, str) and len(x.strip()) > 0)
    )
    
    valid_df = df[valid_mask][required_cols].reset_index(drop=True)
    
    excluded_count = len(df) - len(valid_df)
    if excluded_count > 0:
        logger.debug(f"Excluded {excluded_count} invalid entries from chunk.")
        
    return valid_df


def process_and_save_corpus(
    dataset_name: str = "codeparrot/code-trans-py-js",
    split: str = "train",
    output_path: str = OUTPUT_PATH,
    target_rows: Optional[int] = None
) -> None:
    """
    Process the dataset in chunks, ensuring memory usage stays below the limit,
    and save the final corpus to CSV.
    
    Args:
        dataset_name: HuggingFace dataset identifier.
        split: Dataset split to process.
        output_path: Path to save the final corpus CSV.
        target_rows: Optional target number of rows to collect (for sampling).
    """
    logger.info(f"Starting corpus processing for '{dataset_name}' (split='{split}')...")
    logger.info(f"Memory limit: {MEMORY_LIMIT_GB} GB")
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize streaming iterator
    iterator = load_raw_dataset_streaming(dataset_name, split)
    
    collected_rows: List[Dict[str, Any]] = []
    chunk_buffer: List[Dict[str, Any]] = []
    total_processed = 0
    total_valid = 0
    
    for row in iterator:
        total_processed += 1
        chunk_buffer.append(row)
        
        # Check memory before processing chunk
        current_memory_gb = get_peak_memory_usage_gb()
        if current_memory_gb > MEMORY_LIMIT_GB * 0.9:
            logger.warning(f"Memory usage at {current_memory_gb:.2f} GB (>90% limit). "
                         f"Processing buffered chunk to free memory...")
            process_buffer(chunk_buffer, collected_rows)
            chunk_buffer = []
            gc.collect()
            log_memory_usage(logger)
            
        # Process buffer if it reaches CHUNK_SIZE
        if len(chunk_buffer) >= CHUNK_SIZE:
            process_buffer(chunk_buffer, collected_rows)
            chunk_buffer = []
            gc.collect()
            
            # Check memory after processing
            current_memory_gb = get_peak_memory_usage_gb()
            log_memory_usage(logger)
            if not validate_and_log_memory_constraint(logger, current_memory_gb, MEMORY_LIMIT_GB):
                logger.error("Memory limit exceeded during processing. Stopping.")
                break
        
        # Check target rows if specified
        if target_rows and len(collected_rows) >= target_rows:
            logger.info(f"Reached target rows ({target_rows}). Stopping iteration.")
            break
        
        # Periodic memory check every 1000 rows
        if total_processed % 1000 == 0:
            current_memory_gb = get_peak_memory_usage_gb()
            log_memory_usage(logger)
            if not validate_and_log_memory_constraint(logger, current_memory_gb, MEMORY_LIMIT_GB):
                logger.error("Memory limit exceeded during processing. Stopping.")
                break
    
    # Process remaining buffer
    if chunk_buffer:
        process_buffer(chunk_buffer, collected_rows)
        
    logger.info(f"Processing complete. Total rows processed: {total_processed}")
    logger.info(f"Total valid rows collected: {len(collected_rows)}")
    
    # Save to CSV
    if collected_rows:
        df_final = pd.DataFrame(collected_rows)
        df_final.to_csv(output_path, index=False)
        logger.info(f"Corpus saved to {output_path}")
        
        # Log final memory usage
        final_memory_gb = get_peak_memory_usage_gb()
        log_memory_usage(logger)
        validate_and_log_memory_constraint(logger, final_memory_gb, MEMORY_LIMIT_GB)
    else:
        logger.error("No valid rows collected. Output file not created.")
        raise RuntimeError("Failed to collect any valid rows from the dataset.")


def process_buffer(chunk_buffer: List[Dict[str, Any]], collected_rows: List[Dict[str, Any]]) -> None:
    """
    Process a buffer of rows and add valid entries to the collected rows list.
    
    Args:
        chunk_buffer: List of rows to process.
        collected_rows: List to append valid rows to.
    """
    if not chunk_buffer:
        return
        
    df_chunk = process_chunk(chunk_buffer)
    if not df_chunk.empty:
        collected_rows.extend(df_chunk.to_dict('records'))
        logger.debug(f"Added {len(df_chunk)} valid rows to collection.")


def main():
    """
    Main entry point for the sampling logic script.
    """
    logger.info("=== Starting T013c: Sampling/Chunking Logic ===")
    
    try:
        # Process the dataset with memory constraints
        # Note: We do not specify target_rows here to collect as many as possible
        # within the memory limit. The downstream task T014 will validate the count.
        process_and_save_corpus(
            dataset_name="codeparrot/code-trans-py-js",
            split="train",
            output_path=OUTPUT_PATH
        )
        
        logger.info("=== T013c completed successfully ===")
        
    except Exception as e:
        logger.error(f"=== T013c failed: {e} ===")
        raise


if __name__ == "__main__":
    main()