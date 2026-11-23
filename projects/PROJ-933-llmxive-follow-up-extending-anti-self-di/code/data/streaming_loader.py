"""
Streaming dataset loading and chunked processing utilities.

This module provides functions to load datasets from HuggingFace or other sources
in a streaming fashion to avoid memory issues, and to process them in chunks.
"""
import json
import os
import hashlib
from pathlib import Path
from typing import Dict, Any, Iterator, List, Optional, Callable, Tuple
from collections import defaultdict
import logging

try:
    from datasets import load_dataset
except ImportError:
    raise ImportError(
        "The 'datasets' package is required. Install it via: pip install datasets"
    )

logger = logging.getLogger(__name__)


def stream_dataset(
    dataset_name: str,
    split: str = "train",
    streaming: bool = True,
    cache_dir: Optional[str] = None,
    hf_token: Optional[str] = None
) -> Iterator[Dict[str, Any]]:
    """
    Stream a dataset from HuggingFace without loading it all into memory.

    Args:
        dataset_name: The name of the dataset on HuggingFace Hub.
        split: The dataset split to load (e.g., "train", "test").
        streaming: If True, stream the dataset. If False, load it all.
        cache_dir: Optional directory to cache the dataset.
        hf_token: Optional HuggingFace token for private datasets.

    Yields:
        Dict[str, Any]: Each example from the dataset.

    Raises:
        RuntimeError: If the dataset cannot be fetched from a real source.
    """
    if not streaming:
        logger.warning("Non-streaming mode requested. This may cause memory issues for large datasets.")

    try:
        dataset = load_dataset(
            dataset_name,
            split=split,
            streaming=streaming,
            cache_dir=cache_dir,
            token=hf_token
        )
    except Exception as e:
        raise RuntimeError(
            f"Failed to load dataset '{dataset_name}' from a real source. "
            "No synthetic fallback is allowed. Error: {e}"
        ) from e

    for item in dataset:
        yield item


def stream_dataset_multiple(
    dataset_configs: List[Dict[str, Any]]
) -> Iterator[Tuple[str, Dict[str, Any]]]:
    """
    Stream multiple datasets and yield them with their source name.

    Args:
        dataset_configs: List of dicts with keys: name, split, kwargs (optional).

    Yields:
        Tuple[str, Dict[str, Any]]: (source_name, example)
    """
    for config in dataset_configs:
        name = config["name"]
        split = config.get("split", "train")
        kwargs = config.get("kwargs", {})

        logger.info(f"Streaming dataset: {name} (split={split})")
        for item in stream_dataset(name, split=split, **kwargs):
            yield name, item


def process_in_chunks(
    stream: Iterator[Dict[str, Any]],
    chunk_size: int,
    processor_fn: Callable[[List[Dict[str, Any]]], Any],
    output_path: Optional[str] = None
) -> Iterator[Any]:
    """
    Process a stream of data in chunks.

    Args:
        stream: Iterator of data items.
        chunk_size: Number of items to process at once.
        processor_fn: Function to apply to each chunk.
        output_path: Optional path to write chunk results.

    Yields:
        Results from processor_fn for each chunk.
    """
    chunk = []
    for item in stream:
        chunk.append(item)
        if len(chunk) >= chunk_size:
            result = processor_fn(chunk)
            if output_path:
                write_chunk(result, output_path)
            yield result
            chunk = []

    if chunk:
        result = processor_fn(chunk)
        if output_path:
            write_chunk(result, output_path)
        yield result


def accumulate_statistics(
    stream: Iterator[Dict[str, Any]],
    stats_fn: Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]],
    initial_stats: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Accumulate statistics over a stream of data.

    Args:
        stream: Iterator of data items.
        stats_fn: Function to update stats with a new item.
        initial_stats: Optional initial statistics dict.

    Returns:
        Final accumulated statistics.
    """
    stats = initial_stats or {}
    for item in stream:
        stats = stats_fn(stats, item)
    return stats


def compute_dataset_checksum(
    stream: Iterator[Dict[str, Any]],
    chunk_size: int = 1000
) -> str:
    """
    Compute a checksum of a dataset stream for verification.

    Args:
        stream: Iterator of data items.
        chunk_size: Number of items to hash at once.

    Returns:
        Hexadecimal checksum string.
    """
    hasher = hashlib.sha256()
    chunk = []
    for item in stream:
        chunk.append(json.dumps(item, sort_keys=True))
        if len(chunk) >= chunk_size:
            hasher.update("".join(chunk).encode("utf-8"))
            chunk = []

    if chunk:
        hasher.update("".join(chunk).encode("utf-8"))

    return hasher.hexdigest()


def filter_stream(
    stream: Iterator[Dict[str, Any]],
    filter_fn: Callable[[Dict[str, Any]], bool]
) -> Iterator[Dict[str, Any]]:
    """
    Filter a stream of data based on a predicate function.

    Args:
        stream: Iterator of data items.
        filter_fn: Function that returns True for items to keep.

    Yields:
        Items that pass the filter.
    """
    for item in stream:
        if filter_fn(item):
            yield item


def sample_stream(
    stream: Iterator[Dict[str, Any]],
    sample_size: int,
    seed: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Take a random sample of a stream without loading it all.

    Args:
        stream: Iterator of data items.
        sample_size: Number of items to sample.
        seed: Random seed for reproducibility.

    Returns:
        List of sampled items.
    """
    import random

    if seed is not None:
        random.seed(seed)

    reservoir = []
    for i, item in enumerate(stream):
        if i < sample_size:
            reservoir.append(item)
        else:
            j = random.randint(0, i)
            if j < sample_size:
                reservoir[j] = item

    return reservoir


def get_stream_length_hint(stream: Iterator[Dict[str, Any]]) -> int:
    """
    Attempt to get the length of a stream if possible.

    Args:
        stream: Iterator of data items.

    Returns:
        Estimated length or 0 if unknown.
    """
    # This is a best-effort attempt; many streams don't expose length
    if hasattr(stream, "num_rows"):
        return stream.num_rows
    return 0


def write_chunk(result: Any, output_path: str) -> None:
    """
    Write a chunk result to a file in JSONL format.

    Args:
        result: The result data to write.
        output_path: Path to the output file.
    """
    with open(output_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(result) + "\n")


def merge_chunked_outputs(chunk_dir: str, final_output_path: str) -> None:
    """
    Merge multiple chunked output files into a single file.

    Args:
        chunk_dir: Directory containing chunk files.
        final_output_path: Path to the final merged output file.
    """
    chunk_files = sorted(Path(chunk_dir).glob("chunk_*.jsonl"))
    with open(final_output_path, "w", encoding="utf-8") as outfile:
        for chunk_file in chunk_files:
            with open(chunk_file, "r", encoding="utf-8") as infile:
                for line in infile:
                    outfile.write(line)
            os.remove(chunk_file)  # Clean up after merging
    if chunk_files:
        os.rmdir(chunk_dir)  # Remove empty directory