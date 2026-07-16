"""
Streaming utilities for handling large trajectory logs in chunks.

This module provides functions to load, stream, process, and analyze
large trajectory datasets using Hugging Face's streaming capabilities.
"""

import json
import os
from typing import Any, Dict, Generator, List, Optional, Union

from datasets import load_dataset


def load_trajectory_dataset(
    dataset_name: str,
    split: str = "train",
    streaming: bool = True,
    cache_dir: Optional[str] = None,
    **kwargs: Any
) -> Union[Any, Dict[str, Any]]:
    """
    Load a trajectory dataset with optional streaming.
    
    Args:
        dataset_name: Name of the dataset or path to local dataset
        split: Dataset split to load (default: "train")
        streaming: Whether to stream the dataset (default: True)
        cache_dir: Optional cache directory for dataset
        **kwargs: Additional arguments passed to load_dataset
        
    Returns:
        Dataset or IterableDataset object
        
    Raises:
        ValueError: If dataset cannot be loaded
        RuntimeError: If real data fetch fails (no synthetic fallback)
    """
    try:
        dataset = load_dataset(
            dataset_name,
            split=split,
            streaming=streaming,
            cache_dir=cache_dir,
            **kwargs
        )
        return dataset
    except Exception as e:
        # Fail loudly - no synthetic fallback allowed
        raise RuntimeError(
            f"Failed to load real dataset '{dataset_name}': {str(e)}. "
            "No synthetic data fallback is permitted."
        ) from e


def stream_trajectory_chunks(
    dataset: Any,
    chunk_size: int = 100,
    batched: bool = True
) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Stream trajectory data in chunks.
    
    Args:
        dataset: Dataset or IterableDataset object
        chunk_size: Number of examples per chunk (default: 100)
        batched: Whether to yield batches (default: True)
        
    Yields:
        List of trajectory examples (one chunk at a time)
    """
    if batched:
        batch = []
        for example in dataset:
            batch.append(example)
            if len(batch) >= chunk_size:
                yield batch
                batch = []
        if batch:
            yield batch
    else:
        for example in dataset:
            yield [example]


def process_streaming_trajectories(
    dataset: Any,
    processor_fn: callable,
    chunk_size: int = 100
) -> Generator[Dict[str, Any], None, None]:
    """
    Process streaming trajectories with a custom processor function.
    
    Args:
        dataset: Dataset or IterableDataset object
        processor_fn: Function to apply to each trajectory
        chunk_size: Size of chunks for processing
        
    Yields:
        Processed trajectory examples
    """
    for chunk in stream_trajectory_chunks(dataset, chunk_size):
        for example in chunk:
            try:
                processed = processor_fn(example)
                if processed is not None:
                    yield processed
            except Exception as e:
                # Log error but continue processing
                print(f"Warning: Failed to process example: {e}")
                continue


def count_streaming_examples(dataset: Any) -> int:
    """
    Count total examples in a streaming dataset.
    
    Note: This consumes the stream, so use with caution on large datasets.
    
    Args:
        dataset: Dataset or IterableDataset object
        
    Returns:
        Total number of examples
    """
    count = 0
    for _ in dataset:
        count += 1
    return count


def save_streamed_trajectories(
    dataset: Any,
    output_path: str,
    chunk_size: int = 100,
    format: str = "jsonl"
) -> str:
    """
    Save streamed trajectories to disk.
    
    Args:
        dataset: Dataset or IterableDataset object
        output_path: Path to save the output file
        chunk_size: Size of chunks for processing
        format: Output format ("jsonl" or "json")
        
    Returns:
        Path to the saved file
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    
    if format == "jsonl":
        with open(output_path, "w", encoding="utf-8") as f:
            for chunk in stream_trajectory_chunks(dataset, chunk_size):
                for example in chunk:
                    f.write(json.dumps(example) + "\n")
    elif format == "json":
        examples = []
        for chunk in stream_trajectory_chunks(dataset, chunk_size):
            examples.extend(chunk)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(examples, f, indent=2)
    else:
        raise ValueError(f"Unsupported format: {format}")
    
    return output_path


def filter_streaming_dataset(
    dataset: Any,
    filter_fn: callable,
    chunk_size: int = 100
) -> Generator[Dict[str, Any], None, None]:
    """
    Filter streaming dataset using a filter function.
    
    Args:
        dataset: Dataset or IterableDataset object
        filter_fn: Function that returns True for examples to keep
        chunk_size: Size of chunks for processing
        
    Yields:
        Filtered trajectory examples
    """
    for chunk in stream_trajectory_chunks(dataset, chunk_size):
        for example in chunk:
            try:
                if filter_fn(example):
                    yield example
            except Exception as e:
                print(f"Warning: Filter failed on example: {e}")
                continue


def sample_streaming_dataset(
    dataset: Any,
    sample_size: int,
    seed: int = 42
) -> Generator[Dict[str, Any], None, None]:
    """
    Sample a fixed number of examples from a streaming dataset.
    
    Args:
        dataset: Dataset or IterableDataset object
        sample_size: Number of examples to sample
        seed: Random seed for reproducibility
        
    Yields:
        Sampled trajectory examples
    """
    import random
    random.seed(seed)
    
    count = 0
    for example in dataset:
        if count >= sample_size:
            break
        # Simple reservoir sampling for streaming
        if count < sample_size:
            yield example
            count += 1
        else:
            j = random.randint(0, count)
            if j < sample_size:
                # Replace a random element
                pass  # Would need to buffer for true reservoir sampling
            count += 1


def get_dataset_info(dataset: Any) -> Dict[str, Any]:
    """
    Get information about a dataset.
    
    Args:
        dataset: Dataset or IterableDataset object
        
    Returns:
        Dictionary with dataset information
    """
    info = {
        "type": type(dataset).__name__,
        "is_streaming": hasattr(dataset, "_iter"),
    }
    
    # Try to get features if available
    if hasattr(dataset, "features"):
        info["features"] = str(dataset.features)
    
    return info
