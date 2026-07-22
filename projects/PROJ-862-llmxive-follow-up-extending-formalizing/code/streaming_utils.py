import logging
from typing import Iterator, List, Dict, Any, Optional, Union
from datasets import Dataset, DatasetDict
import itertools

logger = logging.getLogger(__name__)

def stream_dataset(dataset_name: str, split: str = "train") -> Iterator[Dict[str, Any]]:
    """
    Streams a dataset from HuggingFace.
    """
    from datasets import load_dataset
    try:
        ds = load_dataset(dataset_name, split=split, streaming=True)
        return iter(ds)
    except Exception as e:
        logger.error(f"Failed to stream dataset {dataset_name}: {e}")
        raise

def batch_iterator(iterator: Iterator[Dict[str, Any]], batch_size: int) -> Iterator[List[Dict[str, Any]]]:
    """
    Yields batches of items from an iterator.
    """
    batch = []
    for item in iterator:
        batch.append(item)
        if len(batch) == batch_size:
            yield batch
            batch = []
    if batch:
        yield batch

def get_dataset_info(dataset_name: str) -> Dict[str, Any]:
    """
    Returns basic info about a dataset.
    """
    from datasets import load_dataset
    try:
        ds = load_dataset(dataset_name, split="train", streaming=True)
        # Streaming datasets don't always have immediate info, try to peek
        first_item = next(iter(ds))
        return {
            "columns": list(first_item.keys()),
            "sample": first_item
        }
    except Exception as e:
        logger.error(f"Failed to get dataset info: {e}")
        return {}

def filter_streaming_dataset(iterator: Iterator[Dict[str, Any]], predicate) -> Iterator[Dict[str, Any]]:
    """
    Filters a streaming dataset based on a predicate function.
    """
    for item in iterator:
        if predicate(item):
            yield item

def sample_streaming_dataset(iterator: Iterator[Dict[str, Any]], n: int) -> Iterator[Dict[str, Any]]:
    """
    Samples the first n items from a streaming dataset.
    """
    return itertools.islice(iterator, n)

def validate_dataset_structure(iterator: Iterator[Dict[str, Any]], required_columns: List[str]) -> bool:
    """
    Validates that the dataset has the required columns.
    """
    try:
        first_item = next(iterator)
        for col in required_columns:
            if col not in first_item:
                logger.error(f"Missing required column: {col}")
                return False
        return True
    except StopIteration:
        logger.error("Dataset is empty.")
        return False
