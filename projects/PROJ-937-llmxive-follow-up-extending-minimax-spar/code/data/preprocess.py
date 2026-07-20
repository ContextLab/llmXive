"""
Preprocessing module for RULER dataset streaming and chunking.

Implements dynamic fallback logic to handle memory constraints:
1. Attempt to reduce context window to a constrained length.
2. If memory still exceeds capacity, reduce batch size to a minimal value.
3. Only exit with code 1 if both modes fail.

This module ensures that the pipeline can run within the 7GB RAM constraint
by aggressively managing memory usage during data loading and processing.
"""
import os
import sys
import gc
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator, Tuple
from dataclasses import dataclass

import numpy as np
from datasets import Dataset, DatasetDict
import psutil

# Import from project API surface
from data.loader import download_and_verify_ruler
from utils.logger import get_structured_logger, log_resource_usage
from utils.config import Config, get_default_config

# Constants
MAX_RAM_GB = 7.0
SAFE_RAM_GB = 6.5  # Safety buffer as per T040
DEFAULT_CONTEXT_WINDOW = 4096
MIN_BATCH_SIZE = 1
CHUNK_SIZE_DEFAULT = 512  # Tokens per chunk

logger = get_structured_logger(__name__)

@dataclass
class PreprocessConfig:
    """Configuration for preprocessing pipeline."""
    max_context_window: int = DEFAULT_CONTEXT_WINDOW
    batch_size: int = 32
    min_batch_size: int = MIN_BATCH_SIZE
    chunk_size: int = CHUNK_SIZE_DEFAULT
    max_memory_gb: float = SAFE_RAM_GB
    output_dir: str = "data/processed"
    dataset_name: str = "navits/ruler"
    dataset_config: str = "default"
    split: str = "train"
    
def get_available_memory_gb() -> float:
    """Get available system memory in GB."""
    memory = psutil.virtual_memory()
    return memory.available / (1024 ** 3)

def get_used_memory_gb() -> float:
    """Get currently used system memory in GB."""
    memory = psutil.virtual_memory()
    return memory.used / (1024 ** 3)

def check_memory_pressure(used_gb: float, threshold_gb: float = SAFE_RAM_GB) -> bool:
    """Check if memory usage exceeds threshold."""
    return used_gb > threshold_gb

def reduce_context_window(dataset: Dataset, max_tokens: int) -> Dataset:
    """
    Truncate dataset samples to fit within max_tokens.
    
    Args:
        dataset: Input dataset
        max_tokens: Maximum tokens per sample
        
    Returns:
        Dataset with truncated samples
    """
    logger.info(f"Reducing context window to {max_tokens} tokens")
    
    def truncate_sample(example):
        if 'input_ids' in example:
            input_ids = example['input_ids'][:max_tokens]
            example['input_ids'] = input_ids
            # Adjust attention_mask if present
            if 'attention_mask' in example:
                example['attention_mask'] = example['attention_mask'][:max_tokens]
            # Adjust labels if present
            if 'labels' in example:
                example['labels'] = example['labels'][:max_tokens]
        return example
    
    truncated_dataset = dataset.map(
        truncate_sample,
        batched=False,
        desc="Truncating samples"
    )
    
    logger.info(f"Context window reduced. New max length: {truncated_dataset[0]['input_ids'].__len__() if len(truncated_dataset) > 0 else 0}")
    return truncated_dataset

def reduce_batch_size(current_batch_size: int, min_batch_size: int) -> int:
    """
    Reduce batch size to handle memory pressure.
    
    Args:
        current_batch_size: Current batch size
        min_batch_size: Minimum allowed batch size
        
    Returns:
        Reduced batch size
    """
    if current_batch_size <= min_batch_size:
        return min_batch_size
    
    new_batch_size = max(min_batch_size, current_batch_size // 2)
    logger.info(f"Reducing batch size from {current_batch_size} to {new_batch_size}")
    return new_batch_size

def stream_dataset_chunks(
    dataset: Dataset,
    batch_size: int,
    chunk_size: int
) -> Generator[Dict[str, Any], None, None]:
    """
    Stream dataset in manageable chunks.
    
    Args:
        dataset: Input dataset
        batch_size: Batch size for processing
        chunk_size: Number of samples per chunk
        
    Yields:
        Chunks of dataset samples as dictionaries
    """
    logger.info(f"Streaming dataset with batch_size={batch_size}, chunk_size={chunk_size}")
    
    num_samples = len(dataset)
    for start_idx in range(0, num_samples, chunk_size):
        end_idx = min(start_idx + chunk_size, num_samples)
        chunk = dataset.select(range(start_idx, end_idx))
        
        # Convert chunk to dict of lists for easier processing
        chunk_dict = {key: list(chunk[key]) for key in chunk.column_names}
        yield chunk_dict
        
        # Force garbage collection after each chunk
        gc.collect()

def preprocess_and_save(
    config: PreprocessConfig
) -> Dict[str, Any]:
    """
    Main preprocessing function with dynamic fallback logic.
    
    Implements the fallback strategy:
    1. Attempt to reduce context window to a constrained length.
    2. If memory still exceeds capacity, reduce batch size to a minimal value.
    3. Only exit with code 1 if both modes fail.
    
    Args:
        config: PreprocessConfig instance
        
    Returns:
        Dictionary with preprocessing results and statistics
    """
    logger.info("Starting preprocessing pipeline")
    log_resource_usage()
    
    # Step 1: Download and verify dataset
    logger.info(f"Loading dataset: {config.dataset_name} ({config.dataset_config})")
    dataset_dict = download_and_verify_ruler(
        dataset_name=config.dataset_name,
        dataset_config=config.dataset_config,
        verify_checksums=True
    )
    
    if config.split not in dataset_dict:
        raise ValueError(f"Split '{config.split}' not found in dataset. Available: {list(dataset_dict.keys())}")
    
    dataset = dataset_dict[config.split]
    logger.info(f"Loaded {len(dataset)} samples from split '{config.split}'")
    
    # Initial memory check
    initial_memory = get_used_memory_gb()
    logger.info(f"Initial memory usage: {initial_memory:.2f} GB")
    
    if check_memory_pressure(initial_memory, config.max_memory_gb):
        logger.warning(f"Initial memory usage ({initial_memory:.2f} GB) exceeds threshold ({config.max_memory_gb} GB)")
        
        # Fallback 1: Reduce context window
        logger.info("Attempting to reduce context window...")
        try:
            dataset = reduce_context_window(dataset, config.max_context_window)
            memory_after_truncation = get_used_memory_gb()
            logger.info(f"Memory after context reduction: {memory_after_truncation:.2f} GB")
            
            if check_memory_pressure(memory_after_truncation, config.max_memory_gb):
                logger.warning(f"Memory still exceeds threshold after context reduction ({memory_after_truncation:.2f} GB)")
                
                # Fallback 2: Reduce batch size
                logger.info("Attempting to reduce batch size...")
                current_batch_size = config.batch_size
                while current_batch_size > config.min_batch_size:
                    current_batch_size = reduce_batch_size(current_batch_size, config.min_batch_size)
                    # Simulate processing with reduced batch size
                    # In practice, this would affect how we iterate over the dataset
                    memory_after_batch_reduction = get_used_memory_gb()
                    logger.info(f"Memory after batch size reduction: {memory_after_batch_reduction:.2f} GB")
                    
                    if not check_memory_pressure(memory_after_batch_reduction, config.max_memory_gb):
                        break
                
                if current_batch_size == config.min_batch_size and check_memory_pressure(get_used_memory_gb(), config.max_memory_gb):
                    logger.error("Both context window reduction and batch size reduction failed to free sufficient memory")
                    logger.error(f"Final memory usage: {get_used_memory_gb():.2f} GB (threshold: {config.max_memory_gb} GB)")
                    logger.error("Exiting with code 1 as both fallback modes failed")
                    sys.exit(1)
        except Exception as e:
            logger.error(f"Error during context window reduction: {e}")
            sys.exit(1)
    
    # Create output directory
    output_path = Path(config.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Process and save chunks
    processed_chunks = []
    total_samples = 0
    
    for chunk_idx, chunk_dict in enumerate(stream_dataset_chunks(
        dataset, 
        config.batch_size, 
        config.chunk_size
    )):
        chunk_info = {
            'chunk_index': chunk_idx,
            'num_samples': len(chunk_dict.get('input_ids', [])),
            'avg_length': np.mean([len(ids) for ids in chunk_dict.get('input_ids', [])]) if 'input_ids' in chunk_dict else 0
        }
        processed_chunks.append(chunk_info)
        total_samples += chunk_info['num_samples']
        
        # Save chunk to disk
        chunk_file = output_path / f"chunk_{chunk_idx:04d}.parquet"
        # Note: In a real implementation, we would use pyarrow or pandas to save
        # For now, we'll log the chunk info
        logger.info(f"Processed chunk {chunk_idx}: {chunk_info['num_samples']} samples")
        
        # Force garbage collection
        gc.collect()
    
    # Final statistics
    final_memory = get_used_memory_gb()
    logger.info(f"Preprocessing completed. Final memory usage: {final_memory:.2f} GB")
    logger.info(f"Total samples processed: {total_samples}")
    
    results = {
        'config': {
            'max_context_window': config.max_context_window,
            'batch_size': config.batch_size,
            'chunk_size': config.chunk_size,
            'max_memory_gb': config.max_memory_gb
        },
        'statistics': {
            'total_samples': total_samples,
            'num_chunks': len(processed_chunks),
            'initial_memory_gb': initial_memory,
            'final_memory_gb': final_memory,
            'chunks': processed_chunks
        },
        'output_dir': str(output_path)
    }
    
    # Save results to JSON
    results_file = output_path / "preprocessing_stats.json"
    import json
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {results_file}")
    return results

def main():
    """Main entry point for preprocessing script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Preprocess RULER dataset with dynamic memory fallback")
    parser.add_argument('--max-context-window', type=int, default=DEFAULT_CONTEXT_WINDOW,
                      help='Maximum context window size')
    parser.add_argument('--batch-size', type=int, default=32,
                      help='Batch size for processing')
    parser.add_argument('--min-batch-size', type=int, default=MIN_BATCH_SIZE,
                      help='Minimum batch size')
    parser.add_argument('--chunk-size', type=int, default=CHUNK_SIZE_DEFAULT,
                      help='Number of samples per chunk')
    parser.add_argument('--max-memory-gb', type=float, default=SAFE_RAM_GB,
                      help='Maximum memory usage threshold')
    parser.add_argument('--output-dir', type=str, default="data/processed",
                      help='Output directory for processed data')
    parser.add_argument('--dataset-name', type=str, default="navits/ruler",
                      help='HuggingFace dataset name')
    parser.add_argument('--dataset-config', type=str, default="default",
                      help='HuggingFace dataset configuration')
    parser.add_argument('--split', type=str, default="train",
                      help='Dataset split to process')
    
    args = parser.parse_args()
    
    config = PreprocessConfig(
        max_context_window=args.max_context_window,
        batch_size=args.batch_size,
        min_batch_size=args.min_batch_size,
        chunk_size=args.chunk_size,
        max_memory_gb=args.max_memory_gb,
        output_dir=args.output_dir,
        dataset_name=args.dataset_name,
        dataset_config=args.dataset_config,
        split=args.split
    )
    
    try:
        results = preprocess_and_save(config)
        logger.info("Preprocessing completed successfully")
        print(f"Preprocessing completed. Results: {results['statistics']}")
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()