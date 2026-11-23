"""
Preprocessing utilities for dataset capping and 50-token streaming batching.

This module implements memory-safe data processing strategies for the llmXive pipeline,
focusing on streaming data handling and batch processing to prevent OOM errors.
"""

import json
import logging
import sys
import os
import psutil
from pathlib import Path
from typing import List, Dict, Any, Iterator, Optional, Union, Callable
from collections import deque
import itertools

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class BatchSizeError(Exception):
    """Raised when batch size validation fails."""
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

def get_memory_percent() -> float:
    """
    Get memory usage as a percentage of total system memory.

    Returns:
        float: Memory usage percentage (0-100)
    """
    return psutil.virtual_memory().percent

def check_memory_backoff_condition(threshold_percent: float = 80.0) -> bool:
    """
    Check if memory usage exceeds a threshold that warrants backoff.

    Args:
        threshold_percent: Memory usage threshold (0-100)

    Returns:
        bool: True if memory usage exceeds threshold
    """
    return get_memory_percent() >= threshold_percent

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
    if batch_size > 10000:
        raise BatchSizeError(f"Batch size too large, got {batch_size}, max 10000")

def stream_batch(
    examples: Iterator[Dict[str, Any]],
    batch_size: int = 50
) -> Iterator[List[Dict[str, Any]]]:
    """
    Stream examples in fixed-size batches from an iterator.

    This function yields batches of a fixed maximum size from the input stream.
    It processes sequences incrementally to ensure memory usage remains within limits.
    The batching logic itself is the mechanism to prevent OOM - no synthetic fallbacks.

    Args:
        examples: Iterator of example dictionaries
        batch_size: Maximum number of examples per batch (default: 50)

    Yields:
        List of example dictionaries, up to batch_size in length

    Raises:
        BatchSizeError: If batch_size is invalid
    """
    validate_batch_size(batch_size)

    batch = []
    for example in examples:
        batch.append(example)
        if len(batch) >= batch_size:
            yield batch
            batch = []

    # Yield remaining examples as final batch (if any)
    if batch:
        yield batch

def token_batch_stream(
    token_stream: Iterator[Dict[str, Any]],
    batch_size: int = 50
) -> Iterator[List[Dict[str, Any]]]:
    """
    Stream tokens in batches, grouping by sequence boundaries.

    This function processes token streams in batches of a fixed maximum size,
    ensuring that sequences are processed incrementally to prevent OOM.

    Args:
        token_stream: Iterator of token dictionaries
        batch_size: Maximum number of tokens per batch (default: 50)

    Yields:
        List of token dictionaries, up to batch_size in length
    """
    validate_batch_size(batch_size)

    batch = []
    tokens_count = 0

    for token_data in token_stream:
        batch.append(token_data)
        tokens_count += 1

        if tokens_count >= batch_size:
            yield batch
            batch = []
            tokens_count = 0

    # Yield remaining tokens as final batch (if any)
    if batch:
        yield batch

def load_tokens_from_file(file_path: Union[str, Path]) -> Iterator[Dict[str, Any]]:
    """
    Load tokens from a JSONL file as an iterator.

    Args:
        file_path: Path to the JSONL file

    Yields:
        Dictionary for each line in the file

    Raises:
        FileNotFoundError: If the file does not exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Token file not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON at line {line_num}: {e}")
                raise

def stream_tokens_in_batches(
    file_path: Union[str, Path],
    batch_size: int = 50
) -> Iterator[List[Dict[str, Any]]]:
    """
    Stream tokens from a file in batches.

    This function combines load_tokens_from_file and token_batch_stream
    to provide a convenient interface for batch processing.

    Args:
        file_path: Path to the JSONL file
        batch_size: Maximum number of tokens per batch

    Yields:
        List of token dictionaries, up to batch_size in length
    """
    yield from token_batch_stream(load_tokens_from_file(file_path), batch_size)

def merge_entropy_profiles(
    generation_data: List[Dict[str, Any]],
    entropy_data: List[Dict[str, Any]],
    join_keys: List[str] = ['prompt_id', 'token_index']
) -> List[Dict[str, Any]]:
    """
    Merge generation data with entropy profiles.

    Args:
        generation_data: List of generation records
        entropy_data: List of entropy profile records
        join_keys: Keys to use for joining (default: ['prompt_id', 'token_index'])

    Returns:
        List of merged records

    Raises:
        ValueError: If merge fails due to missing keys
    """
    if not generation_data or not entropy_data:
        logger.warning("Empty input data for merge")
        return []

    # Create lookup dictionary from entropy data
    entropy_lookup = {}
    for record in entropy_data:
        key = tuple(record.get(k) for k in join_keys)
        entropy_lookup[key] = record

    # Merge generation data with entropy profiles
    merged = []
    for gen_record in generation_data:
        key = tuple(gen_record.get(k) for k in join_keys)
        merged_record = gen_record.copy()

        if key in entropy_lookup:
            merged_record.update(entropy_lookup[key])
        else:
            # Log warning for missing entropy data
            logger.warning(f"Missing entropy data for key: {key}")

        merged.append(merged_record)

    return merged

def validate_entropy_profile(
    record: Dict[str, Any],
    required_fields: List[str] = None
) -> bool:
    """
    Validate that an entropy profile record contains all required fields.

    Args:
        record: The entropy profile record to validate
        required_fields: List of required field names

    Returns:
        bool: True if record is valid, False otherwise

    Raises:
        ValueError: If required fields are missing or None
    """
    if required_fields is None:
        required_fields = [
            'prompt_id',
            'token_index',
            'sequence_length',
            'layer_entropy_map'
        ]

    for field in required_fields:
        if field not in record:
            raise ValueError(f"Missing required field: {field}")
        if record[field] is None:
            raise ValueError(f"Field '{field}' is None")

    # Validate layer_entropy_map structure
    layer_map = record.get('layer_entropy_map')
    if not isinstance(layer_map, dict):
        raise ValueError(f"layer_entropy_map must be a dict, got {type(layer_map)}")

    for layer_id, entropy_value in layer_map.items():
        if entropy_value is None:
            raise ValueError(f"Entropy value for layer {layer_id} is None")
        if not isinstance(entropy_value, (int, float)):
            raise ValueError(f"Entropy value for layer {layer_id} must be numeric")

    return True

def main():
    """
    Main function to demonstrate preprocessing functionality.
    """
    logger.info("Preprocessing module loaded successfully")

    # Example usage of stream_batch
    def example_iterator():
        for i in range(100):
            yield {'id': i, 'data': f'example_{i}'}

    logger.info("Testing stream_batch with 100 examples, batch_size=50")
    batch_count = 0
    for batch in stream_batch(example_iterator(), batch_size=50):
        batch_count += 1
        logger.info(f"Batch {batch_count}: {len(batch)} examples")

    logger.info(f"Total batches: {batch_count}")

    # Example usage of token_batch_stream
    def example_token_iterator():
        for i in range(150):
            yield {'token_id': i, 'token': f'token_{i}', 'prompt_id': f'prompt_{i // 50}'}

    logger.info("Testing token_batch_stream with 150 tokens, batch_size=50")
    batch_count = 0
    for batch in token_batch_stream(example_token_iterator(), batch_size=50):
        batch_count += 1
        logger.info(f"Token Batch {batch_count}: {len(batch)} tokens")

    logger.info(f"Total token batches: {batch_count}")

    logger.info("Preprocessing demonstration complete")

if __name__ == '__main__':
    main()
