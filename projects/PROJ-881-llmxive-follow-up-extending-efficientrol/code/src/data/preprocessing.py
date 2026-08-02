"""
Preprocessing utilities for dataset loading and batching.

This module provides streaming and batching functions for processing
dataset examples and token sequences with memory safety guarantees.
"""

import json
import logging
import sys
import os
import psutil
from pathlib import Path
from typing import List, Iterator, Any, Optional, Generator, Dict, Union

# Custom exception for batch size issues
class BatchSizeError(Exception):
    """Raised when batch size constraints cannot be met."""
    pass

# Get current RAM usage in GB
def get_current_ram_gb() -> float:
    """
    Get the current RAM usage of the process in gigabytes.
    
    Returns:
        float: Current RAM usage in GB
    """
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 ** 3)

# Validate batch size
def validate_batch_size(batch_size: int, min_threshold: int = 1) -> None:
    """
    Validate that a batch size is above the minimum threshold.
    
    Args:
        batch_size: The proposed batch size
        min_threshold: Minimum acceptable batch size
        
    Raises:
        BatchSizeError: If batch size is below minimum threshold
    """
    if batch_size < min_threshold:
        raise BatchSizeError(f"Batch size {batch_size} is below minimum threshold {min_threshold}")

# Check memory backoff condition
def check_memory_backoff_condition() -> bool:
    """
    Check if we should trigger memory backoff based on current RAM usage.
    
    Returns:
        bool: True if RAM usage is high (> 6GB), False otherwise
    """
    current_ram = get_current_ram_gb()
    return current_ram > 6.0

# Load tokens from file
def load_tokens_from_file(file_path: Union[str, Path]) -> Generator[List[str], None, None]:
    """
    Load token sequences from a JSONL file.
    
    Args:
        file_path: Path to the JSONL file
        
    Yields:
        List[str]: Token sequences from the file
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Token file not found: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    # Handle different possible formats
                    if isinstance(data, dict):
                        if 'tokens' in data:
                            yield data['tokens']
                        elif 'sequence' in data:
                            yield data['sequence']
                        elif 'text' in data:
                            yield data['text'].split()
                    elif isinstance(data, list):
                        yield data
                except json.JSONDecodeError:
                    logging.warning(f"Skipping invalid JSON line: {line[:100]}")

# Stream dataset examples in batches (from T009a)
def stream_batch(data_file: Union[str, Path], batch_size: int = 500) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Stream dataset examples in batches with memory backoff.
    
    This function implements the 500-example batching logic from T009a.
    If a MemoryError is raised, the batch size is halved until a minimum
    threshold is reached.
    
    Args:
        data_file: Path to the JSONL data file
        batch_size: Initial batch size (default: 500)
        
    Yields:
        List[Dict[str, Any]]: Batches of dataset examples
        
    Raises:
        RuntimeError: If batch size drops below minimum threshold
    """
    path = Path(data_file)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {data_file}")
    
    current_batch_size = batch_size
    min_batch_size = 1
    buffer: List[Dict[str, Any]] = []
    
    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            
            try:
                example = json.loads(line)
                buffer.append(example)
                
                if len(buffer) >= current_batch_size:
                    yield buffer
                    buffer = []
                    
            except MemoryError:
                logging.warning(f"MemoryError at line {line_num}, reducing batch size")
                buffer = []
                current_batch_size = max(current_batch_size // 2, min_batch_size)
                
                if current_batch_size < min_batch_size:
                    raise RuntimeError(f"Batch size too small after memory backoff")
            
            except json.JSONDecodeError as e:
                logging.warning(f"Skipping invalid JSON at line {line_num}: {e}")
    
    # Yield remaining items
    if buffer:
        yield buffer

# NEW: Token-level batching function (T009b)
def token_batch_stream(
    tokens_source: Union[str, Path, Generator[List[str], None, None]],
    batch_size: int = 50,
    min_threshold: int = 8
) -> Generator[List[str], None, None]:
    """
    Stream token sequences in batches with memory-aware fallback.
    
    This function implements the 50-token batching logic required by FR-007.
    It processes sequences token-by-token, accumulating them into batches.
    If a MemoryError is raised, the batch size is halved (50 -> 25 -> 12)
    until the minimum threshold (8 tokens) is reached, at which point a
    RuntimeError is raised.
    
    Args:
        tokens_source: Either a file path to a JSONL file with token sequences,
                     or a generator that yields lists of tokens.
        batch_size: Initial batch size in tokens (default: 50)
        min_threshold: Minimum batch size before raising RuntimeError (default: 8)
        
    Yields:
        List[str]: Batches of tokens (lists of token strings)
        
    Raises:
        RuntimeError: If batch size drops below min_threshold
        FileNotFoundError: If tokens_source is a file path that doesn't exist
        ValueError: If tokens_source is neither a file path nor a generator
    """
    current_batch_size = batch_size
    token_buffer: List[str] = []
    
    # Handle different input types
    if isinstance(tokens_source, (str, Path)):
        token_gen = load_tokens_from_file(tokens_source)
    elif hasattr(tokens_source, '__iter__') and hasattr(tokens_source, '__next__'):
        # It's a generator
        token_gen = tokens_source
    else:
        raise ValueError("tokens_source must be a file path or a generator")
    
    # Iterate through token sequences
    for sequence in token_gen:
        # Add each token from the sequence to the buffer
        for token in sequence:
            token_buffer.append(token)
            
            # Check if we have enough tokens for a batch
            if len(token_buffer) >= current_batch_size:
                try:
                    yield token_buffer[:current_batch_size]
                    token_buffer = token_buffer[current_batch_size:]
                except MemoryError:
                    logging.warning(f"MemoryError with batch size {current_batch_size}, reducing")
                    token_buffer = []
                    current_batch_size = max(current_batch_size // 2, min_threshold)
                    
                    if current_batch_size < min_threshold:
                        raise RuntimeError("Batch size too small")
    
    # Yield remaining tokens if any
    if token_buffer:
        yield token_buffer

# Stream tokens in batches (wrapper for token_batch_stream)
def stream_tokens_in_batches(
    data_file: Union[str, Path],
    batch_size: int = 50,
    min_threshold: int = 8
) -> Generator[List[str], None, None]:
    """
    Wrapper function to stream tokens from a file in batches.
    
    Args:
        data_file: Path to JSONL file containing token sequences
        batch_size: Initial batch size in tokens (default: 50)
        min_threshold: Minimum batch size (default: 8)
        
    Yields:
        List[str]: Batches of tokens
    """
    return token_batch_stream(data_file, batch_size, min_threshold)

# Merge entropy profiles (from T025)
def merge_entropy_profiles(
    generation_file: Union[str, Path],
    entropy_files: List[Union[str, Path]],
    output_file: Union[str, Path]
) -> Dict[str, Any]:
    """
    Merge generation data with entropy profiles.
    
    This function performs a 3-way join on prompt_id and token_index
    between generation data and multiple entropy batch files.
    
    Args:
        generation_file: Path to the merged US1 JSONL file
        entropy_files: List of paths to entropy batch JSONL files
        output_file: Path to write the merged output
        
    Returns:
        Dict[str, Any]: Summary statistics of the merge operation
    """
    # Load generation data into memory (keyed by prompt_id, token_index)
    generation_data: Dict[tuple, Dict[str, Any]] = {}
    with open(generation_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                record = json.loads(line)
                key = (record.get('prompt_id'), record.get('token_index'))
                generation_data[key] = record
    
    # Merge entropy data
    merged_count = 0
    unmatched_count = 0
    
    with open(output_file, 'w', encoding='utf-8') as out_f:
        for entropy_file in entropy_files:
            with open(entropy_file, 'r', encoding='utf-8') as ent_f:
                for line in ent_f:
                    if line.strip():
                        entropy_record = json.loads(line)
                        key = (entropy_record.get('prompt_id'), entropy_record.get('token_index'))
                        
                        if key in generation_data:
                            merged_record = {**generation_data[key], **entropy_record}
                            out_f.write(json.dumps(merged_record) + '\n')
                            merged_count += 1
                        else:
                            unmatched_count += 1
    
    return {
        'merged_count': merged_count,
        'unmatched_count': unmatched_count,
        'total_entropy_records': merged_count + unmatched_count
    }

# Validate entropy profile
def validate_entropy_profile(record: Dict[str, Any]) -> bool:
    """
    Validate that an entropy profile record has all required fields.
    
    Args:
        record: Dictionary representing an entropy profile record
        
    Returns:
        bool: True if valid, False otherwise
        
    Raises:
        ValueError: If the record is invalid
    """
    required_fields = ['prompt_id', 'token_index', 'layer_entropy_map']
    
    for field in required_fields:
        if field not in record or record[field] is None:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate layer_entropy_map structure
    if not isinstance(record['layer_entropy_map'], dict):
        raise ValueError("layer_entropy_map must be a dictionary")
    
    for layer_id, entropy_value in record['layer_entropy_map'].items():
        if entropy_value is None:
            raise ValueError(f"Entropy value for layer {layer_id} is None")
        if not isinstance(entropy_value, (int, float)):
            raise ValueError(f"Entropy value for layer {layer_id} is not numeric")
    
    return True

# Main entry point for testing
def main():
    """
    Main function for testing the preprocessing module.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Test preprocessing functions')
    parser.add_argument('--test-file', type=str, help='Path to test data file')
    parser.add_argument('--batch-size', type=int, default=50, help='Initial batch size')
    parser.add_argument('--min-threshold', type=int, default=8, help='Minimum batch size')
    
    args = parser.parse_args()
    
    if args.test_file:
        logging.basicConfig(level=logging.INFO)
        logging.info(f"Testing token_batch_stream with file: {args.test_file}")
        
        batch_count = 0
        total_tokens = 0
        
        try:
            for batch in token_batch_stream(args.test_file, args.batch_size, args.min_threshold):
                batch_count += 1
                total_tokens += len(batch)
                if batch_count <= 5:  # Log first 5 batches
                    logging.info(f"Batch {batch_count}: {len(batch)} tokens")
            
            logging.info(f"Completed: {batch_count} batches, {total_tokens} total tokens")
        except RuntimeError as e:
            logging.error(f"RuntimeError: {e}")
        except Exception as e:
            logging.error(f"Error: {e}")

if __name__ == '__main__':
    main()
