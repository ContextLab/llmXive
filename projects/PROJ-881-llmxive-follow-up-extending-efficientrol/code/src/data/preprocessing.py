"""
Preprocessing module for entropy-guided validity prediction pipeline.

Handles data loading, batch processing, entropy profile merging, and validation.
"""
import json
import logging
from typing import List, Iterator, Any, Optional, Generator, Dict, Union
from pathlib import Path
import numpy as np
from src.utils.validators import EntropyProfile, validate_json_schema, load_and_validate_jsonl
import yaml

# Configure logging
logger = logging.getLogger(__name__)

class BatchSizeError(Exception):
    """Custom exception for invalid batch sizes."""
    pass

def validate_batch_size(batch_size: int) -> int:
    """
    Validate that batch size is within acceptable limits.
    
    Args:
        batch_size: The requested batch size.
        
    Returns:
        The validated batch size.
        
    Raises:
        BatchSizeError: If batch size is <= 0 or > 50.
    """
    if batch_size <= 0:
        raise BatchSizeError(f"Batch size must be positive, got {batch_size}")
    if batch_size > 50:
        raise BatchSizeError(
            f"Batch size {batch_size} exceeds maximum allowed size of 50 "
            "(FR-007: 7GB RAM limit)"
        )
    return batch_size

def stream_tokens_in_batches(
    token_stream: Iterator[List[Dict[str, Any]]], 
    batch_size: int = 50
) -> Iterator[List[Dict[str, Any]]]:
    """
    Stream tokens from an iterator in fixed-size batches.
    
    Args:
        token_stream: Iterator yielding token dictionaries.
        batch_size: Number of tokens per batch (default 50).
        
    Yields:
        Lists of token dictionaries, each of size <= batch_size.
    """
    validate_batch_size(batch_size)
    batch = []
    for token in token_stream:
        batch.append(token)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch

def process_batch_with_entropy(
    batch: List[Dict[str, Any]], 
    model: Any, 
    layer_indices: List[int]
) -> List[Dict[str, Any]]:
    """
    Process a batch of tokens to compute entropy profiles.
    
    Args:
        batch: List of token dictionaries.
        model: The model used for inference.
        layer_indices: List of layer indices to extract probabilities from.
        
    Returns:
        List of token dictionaries with added entropy profiles.
    """
    results = []
    # Placeholder for actual entropy computation logic
    # This would integrate with the model's forward pass hooks
    for token_data in batch:
        token_data['entropy_profile'] = {
            'layers': {
                str(idx): np.nan  # Placeholder - actual implementation computes real entropy
                for idx in layer_indices
            }
        }
        results.append(token_data)
    return results

def stream_process_sequence(
    token_stream: Iterator[List[Dict[str, Any]]], 
    model: Any, 
    layer_indices: List[int], 
    batch_size: int = 50
) -> Generator[Dict[str, Any], None, None]:
    """
    Stream and process a sequence of tokens with entropy calculation.
    
    Args:
        token_stream: Iterator yielding token batches.
        model: The model used for inference.
        layer_indices: List of layer indices to extract probabilities from.
        batch_size: Number of tokens per batch (default 50).
        
    Yields:
        Processed token dictionaries with entropy profiles.
    """
    for batch in stream_tokens_in_batches(token_stream, batch_size):
        processed_batch = process_batch_with_entropy(batch, model, layer_indices)
        for token_data in processed_batch:
            yield token_data

def load_tokens_from_file(file_path: Union[str, Path]) -> Generator[Dict[str, Any], None, None]:
    """
    Load tokens from a JSONL file.
    
    Args:
        file_path: Path to the JSONL file.
        
    Yields:
        Token dictionaries from the file.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Token file not found: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON line: {e}")
                    continue

def merge_entropy_profiles(
    labeled_dataset_path: Union[str, Path], 
    entropy_profiles_path: Union[str, Path], 
    output_path: Union[str, Path],
    schema_path: Union[str, Path]
) -> Path:
    """
    Merge entropy profiles with the labeled dataset.
    
    Args:
        labeled_dataset_path: Path to the labeled dataset JSONL file.
        entropy_profiles_path: Path to the entropy profiles JSONL file.
        output_path: Path for the merged output JSONL file.
        schema_path: Path to the entropy_profile.schema.yaml file.
        
    Returns:
        Path to the created merged output file.
        
    Raises:
        FileNotFoundError: If input files or schema are missing.
        ValueError: If schema validation fails.
    """
    labeled_path = Path(labeled_dataset_path)
    entropy_path = Path(entropy_profiles_path)
    output_file = Path(output_path)
    schema_file = Path(schema_path)
    
    if not labeled_path.exists():
        raise FileNotFoundError(f"Labeled dataset not found: {labeled_dataset_path}")
    if not entropy_path.exists():
        raise FileNotFoundError(f"Entropy profiles not found: {entropy_profiles_path}")
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
    # Load and validate schema
    with open(schema_file, 'r') as f:
        schema = yaml.safe_load(f)
    
    # Create output directory if needed
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Build index of entropy profiles by sequence_id
    entropy_index = {}
    for record in load_and_validate_jsonl(str(entropy_path)):
        seq_id = record.get('sequence_id')
        if seq_id:
            entropy_index[seq_id] = record
    
    merged_count = 0
    with open(output_file, 'w', encoding='utf-8') as out_f:
        for labeled_record in load_and_validate_jsonl(str(labeled_path)):
            seq_id = labeled_record.get('sequence_id')
            if seq_id and seq_id in entropy_index:
                entropy_record = entropy_index[seq_id]
                # Merge the records
                merged_record = {**labeled_record, **entropy_record}
                # Validate against schema
                validate_json_schema(merged_record, schema)
                out_f.write(json.dumps(merged_record) + '\n')
                merged_count += 1
            else:
                logger.warning(f"Missing entropy profile for sequence_id: {seq_id}")
    
    logger.info(f"Merged {merged_count} records to {output_file}")
    return output_file

def validate_entropy_profile(
    record: Dict[str, Any], 
    schema_path: Optional[Union[str, Path]] = None
) -> bool:
    """
    Validate an EntropyProfile record against the schema.
    
    This function ensures that:
    1. The record matches the EntropyProfile schema structure.
    2. All layers and tokens in the record have valid (non-None) entropy values.
    3. No entropy values are missing.
    
    Args:
        record: The dictionary to validate as an EntropyProfile.
        schema_path: Optional path to the entropy_profile.schema.yaml file.
                    If not provided, uses the default path relative to the project.
                    
    Returns:
        True if the record is valid.
        
    Raises:
        ValueError: If any layer/token in the record is None or missing entropy values,
                   or if the record does not conform to the schema.
        FileNotFoundError: If the schema file is not found.
    """
    if schema_path is None:
        schema_path = Path(__file__).parent.parent.parent / "contracts" / "entropy_profile.schema.yaml"
    
    schema_file = Path(schema_path)
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    # Load schema
    with open(schema_file, 'r') as f:
        schema = yaml.safe_load(f)
    
    # Validate structure against schema
    try:
        validate_json_schema(record, schema)
    except ValueError as e:
        raise ValueError(f"Record does not match EntropyProfile schema: {e}")
    
    # Check for None or missing entropy values in layers
    if 'layers' not in record:
        raise ValueError("EntropyProfile record is missing 'layers' field")
    
    layers = record['layers']
    if not isinstance(layers, dict):
        raise ValueError("'layers' field must be a dictionary")
    
    if not layers:
        raise ValueError("EntropyProfile record has empty 'layers' dictionary")
    
    for layer_id, layer_data in layers.items():
        if layer_data is None:
            raise ValueError(f"Layer '{layer_id}' in EntropyProfile record is None")
        
        if not isinstance(layer_data, dict):
            raise ValueError(f"Layer '{layer_id}' data must be a dictionary")
        
        if 'entropy' not in layer_data:
            raise ValueError(f"Layer '{layer_id}' in EntropyProfile record is missing 'entropy' values")
        
        entropy_values = layer_data['entropy']
        
        if entropy_values is None:
            raise ValueError(f"Layer '{layer_id}' in EntropyProfile record has None entropy values")
        
        if not isinstance(entropy_values, list):
            raise ValueError(f"Layer '{layer_id}' entropy must be a list")
        
        if not entropy_values:
            raise ValueError(f"Layer '{layer_id}' in EntropyProfile record has empty entropy list")
        
        for idx, val in enumerate(entropy_values):
            if val is None:
                raise ValueError(
                    f"Layer '{layer_id}', token {idx} in EntropyProfile record "
                    f"has missing (None) entropy value"
                )
            if not isinstance(val, (int, float)):
                raise ValueError(
                    f"Layer '{layer_id}', token {idx} in EntropyProfile record "
                    f"has non-numeric entropy value: {type(val)}"
                )
    
    return True

def main():
    """Main entry point for preprocessing module CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Preprocessing utilities for entropy-guided validity prediction")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Merge command
    merge_parser = subparsers.add_parser('merge', help='Merge entropy profiles with labeled dataset')
    merge_parser.add_argument('--labeled', required=True, help='Path to labeled dataset JSONL')
    merge_parser.add_argument('--entropy', required=True, help='Path to entropy profiles JSONL')
    merge_parser.add_argument('--output', required=True, help='Path for merged output JSONL')
    merge_parser.add_argument('--schema', required=True, help='Path to entropy_profile.schema.yaml')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate entropy profile records')
    validate_parser.add_argument('--input', required=True, help='Path to JSONL file with entropy profiles')
    validate_parser.add_argument('--schema', help='Path to entropy_profile.schema.yaml (optional)')
    
    args = parser.parse_args()
    
    if args.command == 'merge':
        merge_entropy_profiles(args.labeled, args.entropy, args.output, args.schema)
    elif args.command == 'validate':
        schema_path = args.schema if args.schema else None
        count = 0
        error_count = 0
        for record in load_and_validate_jsonl(args.input):
            try:
                validate_entropy_profile(record, schema_path)
                count += 1
            except ValueError as e:
                error_count += 1
                logger.error(f"Validation failed: {e}")
        logger.info(f"Validated {count} records, {error_count} failures")
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
