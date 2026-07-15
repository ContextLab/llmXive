"""
Streaming utilities for chunked/batched iteration over large datasets.

This module provides memory-efficient iteration over datasets that may exceed
available RAM, enabling processing of large reasoning datasets without loading
everything into memory at once.
"""

import logging
from typing import Iterator, List, Dict, Any, Optional, Union
from datasets import Dataset, DatasetDict
import itertools

logger = logging.getLogger(__name__)

# Default batch size for streaming operations
DEFAULT_BATCH_SIZE = 32

# Maximum number of samples to keep in memory at once
MAX_MEMORY_SAMPLES = 1000


def stream_dataset(
    dataset: Union[Dataset, DatasetDict],
    batch_size: int = DEFAULT_BATCH_SIZE,
    streaming: bool = True,
    columns: Optional[List[str]] = None
) -> Iterator[Dict[str, Any]]:
    """
    Stream a dataset in batches to respect RAM limits.
    
    Args:
        dataset: The HuggingFace Dataset or DatasetDict to stream.
        batch_size: Number of samples per batch.
        streaming: If True, use streaming mode (no full download).
        columns: Optional list of columns to include. If None, includes all.
    
    Yields:
        Individual sample dictionaries from the dataset.
    
    Raises:
        ValueError: If the dataset is empty or batch_size is invalid.
    """
    if not hasattr(dataset, 'num_rows') and not hasattr(dataset, '__iter__'):
        raise ValueError("Dataset must be a HuggingFace Dataset or DatasetDict")
    
    if batch_size <= 0:
        raise ValueError(f"batch_size must be positive, got {batch_size}")
    
    # Handle DatasetDict by iterating over splits
    if isinstance(dataset, DatasetDict):
        logger.info(f"Processing DatasetDict with splits: {list(dataset.keys())}")
        for split_name, split_dataset in dataset.items():
            logger.info(f"Processing split '{split_name}' with {split_dataset.num_rows if hasattr(split_dataset, 'num_rows') else 'unknown'} rows")
            yield from _stream_single_dataset(
                split_dataset, batch_size, streaming, columns, split_name
            )
    else:
        # Single Dataset
        logger.info(f"Processing single dataset with {dataset.num_rows if hasattr(dataset, 'num_rows') else 'unknown'} rows")
        yield from _stream_single_dataset(dataset, batch_size, streaming, columns)

def _stream_single_dataset(
    dataset: Dataset,
    batch_size: int,
    streaming: bool,
    columns: Optional[List[str]],
    split_name: Optional[str] = None
) -> Iterator[Dict[str, Any]]:
    """
    Stream a single HuggingFace Dataset.
    
    Args:
        dataset: The Dataset to stream.
        batch_size: Number of samples per batch.
        streaming: If True, use streaming mode.
        columns: Optional list of columns to include.
        split_name: Optional name of the split for logging.
    
    Yields:
        Individual sample dictionaries.
    """
    split_desc = f"split '{split_name}'" if split_name else "dataset"
    
    if streaming:
        logger.debug(f"Streaming {split_desc} in batch mode")
        # Use streaming mode - iterates without downloading entire dataset
        batch_iter = dataset.iter(batch_size=batch_size)
    else:
        logger.debug(f"Loading {split_desc} in chunks")
        # For non-streaming, we still iterate in chunks to avoid loading all at once
        # if the dataset is large but already downloaded
        total_rows = dataset.num_rows
        for start_idx in range(0, total_rows, batch_size):
            end_idx = min(start_idx + batch_size, total_rows)
            batch = dataset.select(range(start_idx, end_idx))
            batch_iter = [batch]
            break  # We'll iterate below
    
    # Process batches
    batch_count = 0
    sample_count = 0
    
    if streaming:
        for batch in dataset.iter(batch_size=batch_size):
            batch_count += 1
            for i in range(len(batch)):
                sample = {col: batch[col][i] for col in batch.column_names}
                if columns:
                    sample = {k: v for k, v in sample.items() if k in columns}
                sample_count += 1
                yield sample
                
                # Log progress periodically
                if sample_count % 10000 == 0:
                    logger.info(f"Processed {sample_count:,} samples from {split_desc}")
    else:
        # Non-streaming: use select for chunked access
        for start_idx in range(0, dataset.num_rows, batch_size):
            end_idx = min(start_idx + batch_size, dataset.num_rows)
            batch = dataset.select(range(start_idx, end_idx))
            batch_count += 1
            
            for i in range(len(batch)):
                sample = {col: batch[col][i] for col in batch.column_names}
                if columns:
                    sample = {k: v for k, v in sample.items() if k in columns}
                sample_count += 1
                yield sample
                
                if sample_count % 10000 == 0:
                    logger.info(f"Processed {sample_count:,} samples from {split_desc}")
    
    logger.info(f"Completed streaming {split_desc}: {sample_count:,} samples in {batch_count} batches")

def get_dataset_info(dataset: Union[Dataset, DatasetDict]) -> Dict[str, Any]:
    """
    Get information about a dataset without loading it into memory.
    
    Args:
        dataset: The Dataset or DatasetDict to inspect.
    
    Returns:
        Dictionary with dataset metadata.
    """
    info = {
        'type': type(dataset).__name__,
        'splits': [],
        'total_rows': 0,
        'columns': [],
        'features': {}
    }
    
    if isinstance(dataset, DatasetDict):
        info['splits'] = list(dataset.keys())
        for split_name, split_dataset in dataset.items():
            split_info = {
                'name': split_name,
                'num_rows': split_dataset.num_rows if hasattr(split_dataset, 'num_rows') else 'unknown',
                'columns': split_dataset.column_names,
                'features': dict(split_dataset.features) if hasattr(split_dataset, 'features') else {}
            }
            info['splits'].append(split_info)
            info['total_rows'] += split_dataset.num_rows if hasattr(split_dataset, 'num_rows') else 0
            if not info['columns']:
                info['columns'] = split_dataset.column_names
    else:
        info['splits'] = ['main']
        info['total_rows'] = dataset.num_rows if hasattr(dataset, 'num_rows') else 'unknown'
        info['columns'] = dataset.column_names
        info['features'] = dict(dataset.features) if hasattr(dataset, 'features') else {}
    
    return info

def batch_iterator(
    data_iterator: Iterator[Dict[str, Any]],
    batch_size: int
) -> Iterator[List[Dict[str, Any]]]:
    """
    Convert an iterator of samples into an iterator of batches.
    
    Args:
        data_iterator: Iterator yielding individual samples.
        batch_size: Number of samples per batch.
    
    Yields:
        Lists of sample dictionaries (batches).
    """
    if batch_size <= 0:
        raise ValueError(f"batch_size must be positive, got {batch_size}")
    
    batch = []
    for sample in data_iterator:
        batch.append(sample)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    
    # Yield remaining samples as final batch
    if batch:
        yield batch

def filter_streaming_dataset(
    dataset: Union[Dataset, DatasetDict],
    filter_fn: callable,
    batch_size: int = DEFAULT_BATCH_SIZE,
    streaming: bool = True
) -> Iterator[Dict[str, Any]]:
    """
    Stream a dataset while filtering samples based on a predicate function.
    
    Args:
        dataset: The Dataset or DatasetDict to stream.
        filter_fn: Function that takes a sample dict and returns True to keep.
        batch_size: Number of samples per batch for iteration.
        streaming: If True, use streaming mode.
    
    Yields:
        Only samples where filter_fn returns True.
    """
    for sample in stream_dataset(dataset, batch_size, streaming):
        if filter_fn(sample):
            yield sample

def sample_streaming_dataset(
    dataset: Union[Dataset, DatasetDict],
    n_samples: Optional[int] = None,
    fraction: Optional[float] = None,
    seed: int = 42,
    batch_size: int = DEFAULT_BATCH_SIZE,
    streaming: bool = True
) -> Iterator[Dict[str, Any]]:
    """
    Sample a subset of a streaming dataset.
    
    Args:
        dataset: The Dataset or DatasetDict to stream.
        n_samples: Exact number of samples to return.
        fraction: Fraction of dataset to return (0.0 to 1.0).
        seed: Random seed for reproducibility.
        batch_size: Number of samples per batch.
        streaming: If True, use streaming mode.
    
    Yields:
        Sampled samples from the dataset.
    
    Raises:
        ValueError: If neither n_samples nor fraction is provided, or both are provided.
    """
    if (n_samples is None and fraction is None) or (n_samples is not None and fraction is not None):
        raise ValueError("Must provide exactly one of n_samples or fraction")
    
    import random
    random.seed(seed)
    
    if n_samples is not None:
        count = 0
        for sample in stream_dataset(dataset, batch_size, streaming):
            if count >= n_samples:
                break
            yield sample
            count += 1
    else:
        # Fraction-based sampling
        for sample in stream_dataset(dataset, batch_size, streaming):
            if random.random() < fraction:
                yield sample

def validate_dataset_structure(
    dataset: Union[Dataset, DatasetDict],
    required_columns: List[str]
) -> Dict[str, Any]:
    """
    Validate that a dataset contains required columns.
    
    Args:
        dataset: The Dataset or DatasetDict to validate.
        required_columns: List of column names that must exist.
    
    Returns:
        Dictionary with validation results.
    
    Raises:
        ValueError: If any required columns are missing.
    """
    results = {
        'valid': True,
        'missing_columns': [],
        'available_columns': [],
        'details': {}
    }
    
    if isinstance(dataset, DatasetDict):
        for split_name, split_dataset in dataset.items():
          split_columns = split_dataset.column_names
          results['available_columns'].extend(split_columns)
          missing = [col for col in required_columns if col not in split_columns]
          if missing:
              results['missing_columns'].extend(missing)
              results['details'][split_name] = {
                  'missing': missing,
                  'available': split_columns
              }
              results['valid'] = False
          else:
              results['details'][split_name] = {
                  'missing': [],
                  'available': split_columns,
                  'status': 'valid'
              }
    else:
        available = dataset.column_names
        results['available_columns'] = available
        missing = [col for col in required_columns if col not in available]
        if missing:
            results['missing_columns'] = missing
            results['valid'] = False
        else:
            results['details'] = {
                'missing': [],
                'available': available,
                'status': 'valid'
            }
    
    if not results['valid']:
        raise ValueError(
            f"Dataset missing required columns: {results['missing_columns']}. "
            f"Available columns: {list(set(results['available_columns']))}"
        )
    
    return results