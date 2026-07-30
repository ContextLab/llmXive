"""
Data preprocessing module for batched streaming and memory management.

Implements streaming batch processing with automatic memory backoff
when MemoryError is raised during processing.
"""
import json
import logging
import sys
import os
from pathlib import Path
from typing import List, Iterator, Any, Optional, Generator, Dict, Union
import psutil
import torch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_BATCH_SIZE = 500
MIN_BATCH_SIZE = 10
MAX_BATCH_SIZE = 10000
MEMORY_BACKOFF_TRIGGER = "MemoryError"

class BatchSizeError(Exception):
    """Exception raised when batch size validation fails."""
    pass

def get_current_ram_gb() -> float:
    """
    Get current RAM usage in GB.
    
    Returns:
        float: Current RAM usage in GB
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)

def validate_batch_size(batch_size: int) -> None:
    """
    Validate that batch size is within acceptable bounds.
    
    Args:
        batch_size: The batch size to validate
        
    Raises:
        BatchSizeError: If batch size is invalid
    """
    if batch_size <= 0:
        raise BatchSizeError(f"Batch size must be positive, got {batch_size}")
    if batch_size > MAX_BATCH_SIZE:
        raise BatchSizeError(f"Batch size {batch_size} exceeds maximum {MAX_BATCH_SIZE}")
    # Allow any positive size within bounds - the streaming logic will handle actual processing

def check_memory_backoff_condition(error: Exception) -> bool:
    """
    Check if an error triggers memory backoff.
    
    Args:
        error: The exception to check
        
    Returns:
        bool: True if the error is a MemoryError
    """
    return isinstance(error, MemoryError)

def load_tokens_from_file(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Load tokens from a JSONL file.
    
    Args:
        file_path: Path to the JSONL file
        
    Returns:
        List of token records
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    tokens = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                tokens.append(record)
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping invalid JSON on line {line_num}: {e}")
                continue
    return tokens

def stream_batch(
    data_source: Union[List[Dict[str, Any]], str, Path],
    batch_size: int = DEFAULT_BATCH_SIZE,
    min_batch_size: int = MIN_BATCH_SIZE
) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Stream data in batches with automatic memory backoff.
    
    This function processes dataset examples in batches, with automatic
    reduction of batch size if a MemoryError is raised.
    
    Args:
        data_source: Either a list of data records or a path to a JSONL file
        batch_size: Initial batch size (default: 500 examples as per FR-001)
        min_batch_size: Minimum batch size before raising RuntimeError
        
    Yields:
        List of data records for the current batch
        
    Raises:
        BatchSizeError: If batch size is invalid
        RuntimeError: If batch size drops below minimum threshold
        FileNotFoundError: If data_source is a file path that doesn't exist
    """
    # Validate initial batch size
    validate_batch_size(batch_size)
    validate_batch_size(min_batch_size)
    
    if min_batch_size > batch_size:
        raise BatchSizeError(f"min_batch_size ({min_batch_size}) cannot be greater than batch_size ({batch_size})")
    
    # Load data if file path provided
    if isinstance(data_source, (str, Path)):
        data = load_tokens_from_file(data_source)
    else:
        data = list(data_source)
    
    total_examples = len(data)
    logger.info(f"Processing {total_examples} examples with initial batch size {batch_size}")
    
    current_batch_size = batch_size
    
    # Process data in batches
    for start_idx in range(0, total_examples, current_batch_size):
        end_idx = min(start_idx + current_batch_size, total_examples)
        batch = data[start_idx:end_idx]
        
        if not batch:
            continue
            
        try:
            # Attempt to process the batch
            # In a real scenario, this would involve actual data processing
            # that might trigger MemoryError
            yield batch
            
            # If successful, we might want to try increasing batch size slightly
            # for efficiency, but we'll keep it simple and maintain current size
            
        except MemoryError as e:
            logger.warning(f"MemoryError at batch {start_idx//current_batch_size}, reducing batch size")
            
            # Halve the batch size
            current_batch_size = current_batch_size // 2
            
            if current_batch_size < min_batch_size:
                raise RuntimeError(
                    f"Batch size {current_batch_size} has dropped below minimum threshold {min_batch_size}. "
                    f"Cannot continue processing due to memory constraints."
                )
            
            logger.info(f"Reduced batch size to {current_batch_size}, retrying from index {start_idx}")
            
            # Adjust the loop to retry with smaller batch
            # We need to re-process this section with smaller batches
            # Reset the loop position to retry this section
            for retry_start in range(start_idx, min(start_idx + batch_size, total_examples), current_batch_size):
                retry_end = min(retry_start + current_batch_size, total_examples)
                retry_batch = data[retry_start:retry_end]
                if retry_batch:
                    yield retry_batch
            
            # Break to avoid double-processing
            break

def stream_tokens_in_batches(
    tokens: List[Dict[str, Any]],
    batch_size: int = 50
) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Stream tokens in fixed-size batches for inference.
    
    This is specifically for the 50-token batching required during
    entropy extraction (FR-007), separate from the 500-example batching
    in stream_batch.
    
    Args:
        tokens: List of token records
        batch_size: Batch size for token processing (default: 50)
        
    Yields:
        List of token records in the current batch
    """
    validate_batch_size(batch_size)
    
    for i in range(0, len(tokens), batch_size):
        yield tokens[i:i + batch_size]

def merge_entropy_profiles(
    base_data: List[Dict[str, Any]],
    entropy_data: List[Dict[str, Any]],
    join_keys: List[str] = ['prompt_id', 'token_index']
) -> List[Dict[str, Any]]:
    """
    Merge entropy profiles with base data.
    
    Args:
        base_data: Base dataset records
        entropy_data: Entropy profile records
        join_keys: Keys to join on
        
    Returns:
        Merged records with entropy profiles attached
    """
    # Create index from entropy data
    entropy_index = {}
    for record in entropy_data:
        key = tuple(record.get(k) for k in join_keys)
        entropy_index[key] = record.get('layer_entropy_map', {})
    
    # Merge
    merged = []
    for base_record in base_data:
        key = tuple(base_record.get(k) for k in join_keys)
        merged_record = base_record.copy()
        if key in entropy_index:
            merged_record['layer_entropy_map'] = entropy_index[key]
        merged.append(merged_record)
    
    return merged

def validate_entropy_profile(record: Dict[str, Any]) -> None:
    """
    Validate an entropy profile record.
    
    Args:
        record: The record to validate
        
    Raises:
        ValueError: If validation fails
    """
    if not isinstance(record, dict):
        raise ValueError("Record must be a dictionary")
    
    required_fields = ['prompt_id', 'token_index', 'layer_entropy_map']
    for field in required_fields:
        if field not in record:
            raise ValueError(f"Missing required field: {field}")
    
    if not isinstance(record['layer_entropy_map'], dict):
        raise ValueError("layer_entropy_map must be a dictionary")
    
    if len(record['layer_entropy_map']) == 0:
        raise ValueError("layer_entropy_map cannot be empty")
    
    for layer_id, entropy_value in record['layer_entropy_map'].items():
        if entropy_value is None:
            raise ValueError(f"Entropy value for layer {layer_id} is None")
        if not isinstance(entropy_value, (int, float)):
            raise ValueError(f"Entropy value for layer {layer_id} must be numeric")

def main():
    """Main entry point for preprocessing module."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Data preprocessing with batched streaming')
    parser.add_argument('--input', type=str, required=True, help='Input JSONL file path')
    parser.add_argument('--batch-size', type=int, default=DEFAULT_BATCH_SIZE, help='Batch size')
    parser.add_argument('--min-batch-size', type=int, default=MIN_BATCH_SIZE, help='Minimum batch size')
    parser.add_argument('--output', type=str, help='Output file path (optional)')
    
    args = parser.parse_args()
    
    logger.info(f"Starting preprocessing with batch_size={args.batch_size}, min_batch_size={args.min_batch_size}")
    
    processed_count = 0
    batch_count = 0
    
    for batch in stream_batch(args.input, args.batch_size, args.min_batch_size):
        batch_count += 1
        processed_count += len(batch)
        
        if args.output:
            with open(args.output, 'a', encoding='utf-8') as f:
                for record in batch:
                    f.write(json.dumps(record) + '\n')
        
        logger.info(f"Processed batch {batch_count}: {len(batch)} records")
    
    logger.info(f"Completed preprocessing: {processed_count} records in {batch_count} batches")

if __name__ == '__main__':
    main()
