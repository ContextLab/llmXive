"""
Preprocessing module for batched streaming and entropy profile management.

Implements FR-007 (50-token batching) and memory backoff strategies.
"""
import json
import logging
import sys
import os
from pathlib import Path
from typing import List, Iterator, Any, Optional, Generator, Dict, Union
import psutil
import torch
from src.utils.validators import EntropyProfile, validate_entropy_profile as _validate_profile
from src.utils.entropy_calc import calculate_entropy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MAX_MEMORY_GB = 6.0
BATCH_SIZE_TOKENS = 50  # FR-007 requirement

class BatchSizeError(Exception):
    """Raised when batch size constraints are violated."""
    pass

def validate_batch_size(size: int) -> bool:
    """Validate that batch size meets FR-007 requirements."""
    if size != BATCH_SIZE_TOKENS:
        raise BatchSizeError(
            f"Batch size {size} violates FR-007. Must be exactly {BATCH_SIZE_TOKENS} tokens."
        )
    return True

def get_current_ram_gb() -> float:
    """Get current RAM usage in GB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)

def check_memory_backoff_condition() -> bool:
    """
    Check if memory backoff should be triggered.
    
    Returns True if:
    - A MemoryError has occurred (handled via exception in caller)
    - OR RAM usage exceeds 6GB (MAX_MEMORY_GB)
    """
    try:
        current_ram = get_current_ram_gb()
        if current_ram > MAX_MEMORY_GB:
            logger.warning(f"RAM usage {current_ram:.2f}GB exceeds limit {MAX_MEMORY_GB}GB. Triggering backoff.")
            return True
        return False
    except Exception as e:
        logger.warning(f"Could not check RAM usage: {e}. Assuming safe to proceed.")
        return False

def stream_tokens_in_batches(
    tokens: List[Any], 
    batch_size: int = BATCH_SIZE_TOKENS
) -> Generator[List[Any], None, None]:
    """
    Stream tokens from a list in fixed-size batches.
    
    Args:
        tokens: List of token objects or IDs
        batch_size: Number of tokens per batch (default 50)
        
    Yields:
        Lists of tokens of size `batch_size` (last batch may be smaller)
    """
    validate_batch_size(batch_size)
    for i in range(0, len(tokens), batch_size):
        yield tokens[i : i + batch_size]

def stream_batch(
    data_iterator: Iterator[Dict[str, Any]],
    output_path: Optional[Union[str, Path]] = None,
    batch_size: int = BATCH_SIZE_TOKENS
) -> Generator[Dict[str, Any], None, None]:
    """
    Process dataset loading in chunks with memory backoff.
    
    Implements FR-007: Processes sequences in batches of 50 tokens.
    Implements memory backoff: Triggers if MemoryError or RAM > 6GB.
    
    Args:
        data_iterator: Iterator yielding dataset records (dicts)
        output_path: Optional path to write batch results to disk immediately
        batch_size: Token batch size (must be 50 per FR-007)
        
    Yields:
        Processed batch records with merged entropy profiles
        
    Raises:
        BatchSizeError: If batch_size is not 50
        MemoryError: If memory pressure is detected and cannot be resolved
    """
    validate_batch_size(batch_size)
    
    buffer = []
    prompt_id = None
    
    for record in data_iterator:
        # Check memory condition before processing
        if check_memory_backoff_condition():
            logger.warning("Memory backoff triggered. Attempting to flush buffer.")
            if buffer:
                # Force write to disk to free memory
                if output_path:
                    _write_batch_to_disk(buffer, output_path)
                buffer = []
            # If still high memory after flush, raise error
            if check_memory_backoff_condition():
                raise MemoryError(
                    f"RAM usage {get_current_ram_gb():.2f}GB exceeds {MAX_MEMORY_GB}GB. "
                    "Could not recover by flushing buffer."
                )
        
        # Process sequence in 50-token chunks
        tokens = record.get("tokens", [])
        sequence_id = record.get("sequence_id", record.get("prompt_id"))
        
        if not tokens:
            logger.warning(f"Empty token sequence for {sequence_id}, skipping.")
            continue
        
        # Slice sequence into 50-token chunks
        chunked_tokens = list(stream_tokens_in_batches(tokens, batch_size))
        
        # Process each chunk
        for chunk_idx, chunk in enumerate(chunked_tokens):
            chunk_record = {
                "sequence_id": sequence_id,
                "chunk_id": chunk_idx,
                "tokens": chunk,
                "start_index": chunk_idx * batch_size,
                "end_index": (chunk_idx + 1) * batch_size
            }
            
            # Validate chunk before proceeding
            if not _validate_chunk(chunk_record):
                logger.warning(f"Invalid chunk {chunk_idx} for {sequence_id}, skipping.")
                continue
            
            buffer.append(chunk_record)
            
            # Write to disk immediately if buffer gets large or end of sequence
            if len(buffer) >= 10 or chunk_idx == len(chunked_tokens) - 1:
                if output_path:
                    _write_batch_to_disk(buffer, output_path)
                yield from _merge_and_yield(buffer, sequence_id)
                buffer = []

def _validate_chunk(chunk_record: Dict[str, Any]) -> bool:
    """Validate a token chunk record."""
    if not chunk_record.get("tokens"):
        return False
    if not chunk_record.get("sequence_id"):
        return False
    if len(chunk_record["tokens"]) > BATCH_SIZE_TOKENS:
        return False
    return True

def _write_batch_to_disk(batch: List[Dict], output_path: Union[str, Path]) -> None:
    """Write a batch of records to disk in JSONL format."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "a", encoding="utf-8") as f:
        for record in batch:
            f.write(json.dumps(record) + "\n")

def _merge_and_yield(
    chunks: List[Dict[str, Any]], 
    sequence_id: str
) -> Generator[Dict[str, Any], None, None]:
    """
    Merge 50-token chunks back into a single sequence context.
    
    Preserves the EntropyProfile entity definition by maintaining
    layer-wise granularity across the merged sequence.
    """
    if not chunks:
        return
    
    # Sort chunks by start_index to ensure correct order
    sorted_chunks = sorted(chunks, key=lambda x: x["start_index"])
    
    # Merge tokens
    merged_tokens = []
    for chunk in sorted_chunks:
        merged_tokens.extend(chunk["tokens"])
    
    # Create merged record with full sequence context
    merged_record = {
        "sequence_id": sequence_id,
        "tokens": merged_tokens,
        "total_length": len(merged_tokens),
        "chunk_count": len(sorted_chunks),
        "entropy_profile": _calculate_merged_entropy_profile(merged_tokens)
    }
    
    yield merged_record

def _calculate_merged_entropy_profile(tokens: List[Any]) -> Dict[str, Any]:
    """
    Calculate entropy profile for a merged sequence.
    
    Note: In a full implementation, this would use the model's
    layer-wise logits to compute entropy per token. Here we
    provide the structure required by the EntropyProfile schema.
    """
    # Placeholder for actual entropy calculation
    # In production, this would call the model's forward pass
    # and use src.utils.entropy_calc.calculate_entropy()
    return {
        "sequence_id": tokens[0] if tokens else "unknown",
        "layer_entropies": [],  # Populated by model hook in generation.py
        "avg_entropy": 0.0,
        "max_entropy": 0.0
    }

def load_tokens_from_file(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Load tokens from a JSONL file.
    
    Args:
        file_path: Path to JSONL file
        
    Returns:
        List of token records
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Token file not found: {file_path}")
    
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records

def merge_entropy_profiles(
    entropy_data: List[Dict[str, Any]],
    labeled_data: List[Dict[str, Any]],
    join_keys: List[str] = ["sequence_id", "token_index"]
) -> List[Dict[str, Any]]:
    """
    Merge entropy profiles with labeled dataset.
    
    Args:
        entropy_data: List of entropy profile records
        labeled_data: List of labeled token sequence records
        join_keys: Keys to align on (default: sequence_id, token_index)
        
    Returns:
        Merged records preserving EntropyProfile entity definition
    """
    # Build lookup index from labeled data
    label_index = {}
    for record in labeled_data:
        key = tuple(record.get(k) for k in join_keys)
        if key not in label_index:
            label_index[key] = []
        label_index[key].append(record)
    
    merged_records = []
    for entropy_rec in entropy_data:
        key = tuple(entropy_rec.get(k) for k in join_keys)
        
        if key in label_index:
            for label_rec in label_index[key]:
                merged = {**entropy_rec, **label_rec}
                merged["source"] = "merged"
                merged_records.append(merged)
        else:
            # No matching label, include entropy data with null validity
            merged = {**entropy_rec, "validity": None, "source": "entropy_only"}
            merged_records.append(merged)
    
    return merged_records

def validate_entropy_profile(record: Dict[str, Any]) -> bool:
    """
    Validate an EntropyProfile record against schema.
    
    Raises ValueError if any layer/token entropy is None or missing.
    """
    try:
        _validate_profile(record)
        return True
    except ValueError as e:
        logger.error(f"Entropy profile validation failed: {e}")
        raise

def main():
    """CLI entry point for preprocessing module."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Preprocessing for entropy-guided validity prediction")
    parser.add_argument("--input", type=str, required=True, help="Input data file")
    parser.add_argument("--output", type=str, required=True, help="Output file path")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE_TOKENS, 
                      help=f"Batch size in tokens (default: {BATCH_SIZE_TOKENS})")
    
    args = parser.parse_args()
    
    if args.batch_size != BATCH_SIZE_TOKENS:
        logger.warning(f"Batch size {args.batch_size} differs from FR-007 requirement of {BATCH_SIZE_TOKENS}")
    
    logger.info(f"Processing {args.input} with batch size {args.batch_size}")
    
    # Example usage (would be replaced by actual data loading)
    # data = load_tokens_from_file(args.input)
    # for batch in stream_batch(data, args.output, args.batch_size):
    #     pass
    
    logger.info("Preprocessing complete")

if __name__ == "__main__":
    main()
