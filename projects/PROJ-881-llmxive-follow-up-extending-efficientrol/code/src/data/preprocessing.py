"""
Preprocessing module for dataset capping and token batching.
Implements memory-adaptive batching logic as per T009 requirements.
"""

import json
import logging
import sys
import os
import psutil
from pathlib import Path
from typing import List, Dict, Any, Iterator, Optional, Union
from dataclasses import dataclass
import math

# Configure logging for this module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_MAX_EXAMPLES = 500
DEFAULT_MAX_TOKENS = 50
MIN_BATCH_SIZE = 10  # Minimum viable batch size for token batching
MIN_EXAMPLES = 1     # Minimum viable example batch size
MEMORY_THRESHOLD = 90.0  # Percentage of RAM usage that triggers backoff

@dataclass
class BatchSizeError(Exception):
    """Custom exception for batch size validation errors."""
    message: str
    current_size: int
    min_size: int

def get_current_ram_gb() -> float:
    """
    Get current RAM usage in GB.
    
    Returns:
        float: Current RAM usage in GB.
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)

def get_memory_percent() -> float:
    """
    Get current memory usage percentage.
    
    Returns:
        float: Memory usage percentage (0-100).
    """
    return psutil.virtual_memory().percent

def check_memory_backoff_condition() -> bool:
    """
    Check if memory usage exceeds the threshold for backoff.
    
    Returns:
        bool: True if memory usage > 90%, False otherwise.
    """
    return get_memory_percent() > MEMORY_THRESHOLD

def validate_batch_size(batch_size: int, min_size: int) -> None:
    """
    Validate that batch size is above minimum threshold.
    
    Args:
        batch_size: The batch size to validate.
        min_size: The minimum allowed batch size.
        
    Raises:
        BatchSizeError: If batch size is below minimum.
    """
    if batch_size < min_size:
        raise BatchSizeError(
            f"Batch size {batch_size} is below minimum threshold {min_size}",
            current_size=batch_size,
            min_size=min_size
        )

def stream_batch(
    examples: Union[List[Dict[str, Any]], Iterator[Dict[str, Any]]],
    max_examples: int = DEFAULT_MAX_EXAMPLES
) -> Iterator[List[Dict[str, Any]]]:
    """
    Stream examples in batches with adaptive memory management.
    
    If memory usage exceeds 90%, the batch size is halved until it reaches
    the minimum threshold. If the batch size drops below the minimum,
    a RuntimeError is raised.
    
    Args:
        examples: List or iterator of example dictionaries.
        max_examples: Maximum number of examples per batch (default: 500).
        
    Yields:
        List[Dict[str, Any]]: Batches of examples.
        
    Raises:
        RuntimeError: If batch size drops below minimum threshold.
    """
    # Convert iterator to list if needed for length calculation
    if not isinstance(examples, list):
        examples = list(examples)
    
    total_examples = len(examples)
    batch_size = min(max_examples, total_examples)
    
    # Validate initial batch size
    validate_batch_size(batch_size, MIN_EXAMPLES)
    
    logger.info(f"Starting stream_batch with {total_examples} examples, initial batch_size={batch_size}")
    
    start_idx = 0
    while start_idx < total_examples:
        # Check memory before processing batch
        if check_memory_backoff_condition():
            logger.warning(f"High memory usage ({get_memory_percent():.1f}%), reducing batch size")
            batch_size = max(MIN_EXAMPLES, batch_size // 2)
            validate_batch_size(batch_size, MIN_EXAMPLES)
            logger.info(f"Reduced batch size to {batch_size}")
        
        end_idx = min(start_idx + batch_size, total_examples)
        batch = examples[start_idx:end_idx]
        
        if not batch:
            break
            
        yield batch
        start_idx = end_idx

def token_batch_stream(
    tokens: Union[List[str], Iterator[str]],
    max_tokens: int = DEFAULT_MAX_TOKENS
) -> Iterator[List[str]]:
    """
    Stream tokens in fixed-size batches with adaptive memory management.
    
    Enforces a fixed number of tokens per batch. If memory usage exceeds 90%,
    the batch size is halved until it reaches the minimum of 10 tokens.
    Only raises RuntimeError if batch size drops below the minimum viable threshold.
    
    Args:
        tokens: List or iterator of token strings.
        max_tokens: Maximum number of tokens per batch (default: 50).
        
    Yields:
        List[str]: Batches of tokens.
        
    Raises:
        RuntimeError: If batch size drops below minimum threshold (10 tokens).
    """
    # Convert iterator to list if needed for length calculation
    if not isinstance(tokens, list):
        tokens = list(tokens)
    
    total_tokens = len(tokens)
    batch_size = min(max_tokens, total_tokens)
    
    # Validate initial batch size
    validate_batch_size(batch_size, MIN_BATCH_SIZE)
    
    logger.info(f"Starting token_batch_stream with {total_tokens} tokens, initial batch_size={batch_size}")
    
    start_idx = 0
    while start_idx < total_tokens:
        # Check memory before processing batch
        if check_memory_backoff_condition():
            logger.warning(f"High memory usage ({get_memory_percent():.1f}%), reducing batch size")
            batch_size = max(MIN_BATCH_SIZE, batch_size // 2)
            validate_batch_size(batch_size, MIN_BATCH_SIZE)
            logger.info(f"Reduced token batch size to {batch_size}")
        
        end_idx = min(start_idx + batch_size, total_tokens)
        batch = tokens[start_idx:end_idx]
        
        if not batch:
            break
            
        yield batch
        start_idx = end_idx

def load_tokens_from_file(file_path: Union[str, Path]) -> List[str]:
    """
    Load tokens from a JSONL file where each line is a JSON object with a 'tokens' field.
    
    Args:
        file_path: Path to the JSONL file.
        
    Returns:
        List[str]: List of tokens.
        
    Raises:
        FileNotFoundError: If file does not exist.
        json.JSONDecodeError: If file contains invalid JSON.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Token file not found: {file_path}")
    
    tokens = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                if 'tokens' in record:
                    tokens.extend(record['tokens'])
                elif 'token' in record:
                    tokens.append(record['token'])
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing line {line_num}: {e}")
                raise
    
    return tokens

def stream_tokens_in_batches(
    file_path: Union[str, Path],
    max_tokens: int = DEFAULT_MAX_TOKENS
) -> Iterator[List[str]]:
    """
    Stream tokens from a file in batches.
    
    Args:
        file_path: Path to the JSONL file.
        max_tokens: Maximum tokens per batch.
        
    Yields:
        List[str]: Batches of tokens.
    """
    tokens = load_tokens_from_file(file_path)
    yield from token_batch_stream(tokens, max_tokens)

def merge_entropy_profiles(
    generation_data: List[Dict[str, Any]],
    entropy_data: List[Dict[str, Any]],
    join_keys: List[str] = ['prompt_id', 'token_index']
) -> List[Dict[str, Any]]:
    """
    Merge generation data with entropy profiles.
    
    Args:
        generation_data: List of generation records.
        entropy_data: List of entropy profile records.
        join_keys: Keys to join on (default: ['prompt_id', 'token_index']).
        
    Returns:
        List[Dict[str, Any]]: Merged records.
    """
    # Create lookup dictionary for entropy data
    entropy_lookup = {}
    for record in entropy_data:
        key = tuple(record.get(k) for k in join_keys)
        entropy_lookup[key] = record
    
    merged = []
    for gen_record in generation_data:
        key = tuple(gen_record.get(k) for k in join_keys)
        merged_record = gen_record.copy()
        
        if key in entropy_lookup:
            merged_record.update(entropy_lookup[key])
        
        merged.append(merged_record)
    
    return merged

def validate_entropy_profile(
    profile: Dict[str, Any],
    schema_path: Optional[Union[str, Path]] = None
) -> bool:
    """
    Validate an entropy profile record against the schema.
    
    Args:
        profile: The entropy profile record to validate.
        schema_path: Optional path to schema file.
        
    Returns:
        bool: True if valid, False otherwise.
        
    Raises:
        ValueError: If profile is invalid.
    """
    # Check required fields
    required_fields = ['prompt_id', 'token_index', 'sequence_length', 'layer_entropy_map']
    for field in required_fields:
        if field not in profile:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate layer_entropy_map
    layer_entropy_map = profile.get('layer_entropy_map')
    if layer_entropy_map is None:
        raise ValueError("layer_entropy_map cannot be None")
    
    if not isinstance(layer_entropy_map, dict):
        raise ValueError("layer_entropy_map must be a dictionary")
    
    # Check that all entropy values are not None
    for layer_id, entropy_value in layer_entropy_map.items():
        if entropy_value is None:
            raise ValueError(f"Entropy value for layer {layer_id} is None")
        if not isinstance(entropy_value, (int, float)):
            raise ValueError(f"Entropy value for layer {layer_id} must be numeric")
    
    return True

def main():
    """
    Main function for testing preprocessing functions.
    """
    logger.info("Testing preprocessing functions...")
    
    # Test stream_batch
    test_examples = [{'id': i, 'data': f'example_{i}'} for i in range(100)]
    batches = list(stream_batch(test_examples, max_examples=20))
    logger.info(f"stream_batch produced {len(batches)} batches")
    
    # Test token_batch_stream
    test_tokens = [f'token_{i}' for i in range(100)]
    token_batches = list(token_batch_stream(test_tokens, max_tokens=10))
    logger.info(f"token_batch_stream produced {len(token_batches)} batches")
    
    # Test memory backoff simulation
    logger.info(f"Current memory usage: {get_memory_percent():.1f}%")
    
    logger.info("Preprocessing tests completed successfully")

if __name__ == '__main__':
    main()
