"""
Data preprocessing module for batched streaming and memory management.

Implements streaming mechanisms that process sequences in fixed batches,
with automatic memory backoff when MemoryError is encountered.
"""

import json
import logging
import sys
import os
from pathlib import Path
from typing import List, Iterator, Any, Optional, Generator, Dict, Union

# Custom exception for batch size issues
class BatchSizeError(Exception):
    """Raised when batch size validation fails."""
    pass

logger = logging.getLogger(__name__)

def validate_batch_size(batch_size: int, min_size: int = 1, max_size: int = 10000) -> None:
    """
    Validate that batch size is within acceptable bounds.
    
    Args:
        batch_size: The proposed batch size
        min_size: Minimum allowed batch size
        max_size: Maximum allowed batch size
        
    Raises:
        BatchSizeError: If batch size is out of bounds
    """
    if batch_size < min_size:
        raise BatchSizeError(f"Batch size {batch_size} is below minimum {min_size}")
    if batch_size > max_size:
        raise BatchSizeError(f"Batch size {batch_size} exceeds maximum {max_size}")

def stream_tokens_in_batches(
    tokens: Union[List[str], Generator[str, None, None]], 
    batch_size: int
) -> Iterator[List[str]]:
    """
    Stream tokens in fixed-size batches.
    
    Args:
        tokens: List or generator of tokens to batch
        batch_size: Number of tokens per batch
        
    Yields:
        Lists of tokens, each of size at most batch_size
    """
    validate_batch_size(batch_size)
    
    if isinstance(tokens, list):
        for i in range(0, len(tokens), batch_size):
            yield tokens[i:i + batch_size]
    else:
        # Handle generator case
        batch = []
        for token in tokens:
            batch.append(token)
            if len(batch) >= batch_size:
                yield batch
                batch = []
        if batch:
            yield batch

def stream_batch(
    data_source: Union[str, Path, List[Dict[str, Any]]],
    batch_size: int = 100,
    output_path: Optional[Union[str, Path]] = None,
    min_batch_size: int = 10,
    reduction_factor: float = 0.5
) -> Generator[Dict[str, Any], None, None]:
    """
    Stream data in batches with automatic memory backoff.
    
    This function processes sequences in fixed batches of a manageable token count.
    If a MemoryError is caught, it reduces the batch size by a significant margin
    and retries.
    
    Args:
        data_source: Path to JSONL file or list of data records
        batch_size: Initial batch size for processing
        output_path: Optional path to write batched output
        min_batch_size: Minimum batch size before failing
        reduction_factor: Factor to reduce batch size on MemoryError (0.5 = halve)
        
    Yields:
        Batches of data records
        
    Raises:
        MemoryError: If batch size cannot be reduced further
        FileNotFoundError: If data source file doesn't exist
        BatchSizeError: If initial batch size is invalid
    """
    validate_batch_size(batch_size)
    
    current_batch_size = batch_size
    data_iter = None
    
    # Prepare data iterator
    if isinstance(data_source, (str, Path)):
        data_path = Path(data_source)
        if not data_path.exists():
            raise FileNotFoundError(f"Data source not found: {data_path}")
        
        def file_generator():
            with open(data_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        yield json.loads(line)
        
        data_iter = file_generator()
    elif isinstance(data_source, list):
        data_iter = iter(data_source)
    else:
        raise TypeError(f"Unsupported data source type: {type(data_source)}")
    
    # Prepare output file if specified
    output_file = None
    if output_path:
        output_file = open(output_path, 'w', encoding='utf-8')
    
    try:
        batch = []
        for record in data_iter:
            batch.append(record)
            
            if len(batch) >= current_batch_size:
                yield batch
                
                if output_file:
                    for rec in batch:
                        output_file.write(json.dumps(rec) + '\n')
                
                batch = []
        
        # Yield remaining items
        if batch:
            yield batch
            
            if output_file:
                for rec in batch:
                    output_file.write(json.dumps(rec) + '\n')
    
    except MemoryError as e:
        logger.warning(f"MemoryError encountered with batch size {current_batch_size}: {e}")
        
        if output_file:
            output_file.close()
        
        # Reduce batch size and retry
        new_batch_size = max(min_batch_size, int(current_batch_size * reduction_factor))
        
        if new_batch_size >= current_batch_size:
            raise MemoryError(
                f"Cannot reduce batch size further. Current: {current_batch_size}, "
                f"Minimum: {min_batch_size}"
            ) from e
        
        logger.info(f"Retrying with reduced batch size: {new_batch_size}")
        
        # Recreate iterator and retry with smaller batch
        if isinstance(data_source, (str, Path)):
            data_iter = file_generator()
        else:
            data_iter = iter(data_source)
        
        # Recursively call with smaller batch size
        yield from stream_batch(
            data_source=data_iter,
            batch_size=new_batch_size,
            output_path=output_path,
            min_batch_size=min_batch_size,
            reduction_factor=reduction_factor
        )
    
    finally:
        if output_file:
            output_file.close()

def load_tokens_from_file(file_path: Union[str, Path]) -> Iterator[str]:
    """
    Load tokens from a JSONL file where each line contains a token.
    
    Args:
        file_path: Path to the JSONL file
        
    Yields:
        Individual tokens as strings
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Token file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    token = json.loads(line)
                    if isinstance(token, str):
                        yield token
                    elif isinstance(token, dict) and 'token' in token:
                        yield token['token']
                except json.JSONDecodeError:
                    # Assume raw token if not JSON
                    yield line

def merge_entropy_profiles(
    entropy_profiles_path: Union[str, Path],
    labeled_dataset_path: Union[str, Path],
    output_path: Union[str, Path]
) -> None:
    """
    Merge entropy profiles with labeled dataset.
    
    Args:
        entropy_profiles_path: Path to entropy profiles JSONL file
        labeled_dataset_path: Path to labeled dataset JSONL file
        output_path: Path for merged output JSONL file
    """
    entropy_profiles_path = Path(entropy_profiles_path)
    labeled_dataset_path = Path(labeled_dataset_path)
    output_path = Path(output_path)
    
    if not entropy_profiles_path.exists():
        raise FileNotFoundError(f"Entropy profiles not found: {entropy_profiles_path}")
    if not labeled_dataset_path.exists():
        raise FileNotFoundError(f"Labeled dataset not found: {labeled_dataset_path}")
    
    # Load entropy profiles into dict by sequence_id
    entropy_dict = {}
    with open(entropy_profiles_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                record = json.loads(line)
                seq_id = record.get('sequence_id') or record.get('prompt_id')
                if seq_id:
                    entropy_dict[seq_id] = record
    
    # Merge with labeled dataset
    with open(output_path, 'w', encoding='utf-8') as out_f:
        with open(labeled_dataset_path, 'r', encoding='utf-8') as in_f:
            for line in in_f:
                line = line.strip()
                if line:
                    record = json.loads(line)
                    seq_id = record.get('sequence_id') or record.get('prompt_id')
                    
                    if seq_id and seq_id in entropy_dict:
                        # Merge entropy data
                        merged_record = {**record, **entropy_dict[seq_id]}
                        # Remove duplicate keys that might conflict
                        if 'sequence_id' in merged_record and 'prompt_id' in merged_record:
                            if merged_record['sequence_id'] != merged_record['prompt_id']:
                                logger.warning(
                                    f"Sequence ID mismatch for {seq_id}: "
                                    f"sequence_id={merged_record['sequence_id']}, "
                                    f"prompt_id={merged_record['prompt_id']}"
                                )
                    
                    else:
                        merged_record = record
                    
                    out_f.write(json.dumps(merged_record) + '\n')
    
    logger.info(f"Merged dataset written to {output_path}")

def validate_entropy_profile(record: Dict[str, Any]) -> bool:
    """
    Validate an entropy profile record against schema requirements.
    
    Args:
        record: The entropy profile record to validate
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If record is invalid
    """
    required_fields = ['prompt_id', 'entropy_values']
    
    for field in required_fields:
        if field not in record:
            raise ValueError(f"Missing required field: {field}")
    
    if not isinstance(record['prompt_id'], str):
        raise ValueError("prompt_id must be a string")
    
    if not isinstance(record['entropy_values'], list):
        raise ValueError("entropy_values must be a list")
    
    for i, val in enumerate(record['entropy_values']):
        if val is None:
            raise ValueError(f"entropy_values[{i}] is None")
        if not isinstance(val, (int, float)):
            raise ValueError(f"entropy_values[{i}] is not numeric: {type(val)}")
    
    return True

def main():
    """Main entry point for preprocessing module."""
    logging.basicConfig(level=logging.INFO)
    
    # Example usage demonstration
    logger.info("Preprocessing module loaded successfully")
    
    # Test with sample data if arguments provided
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        
        logger.info(f"Processing {input_file} with streaming batches")
        
        for i, batch in enumerate(stream_batch(input_file, batch_size=50, output_path=output_file)):
            logger.info(f"Processed batch {i+1}: {len(batch)} records")

if __name__ == "__main__":
    main()
