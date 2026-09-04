"""
RoboDojo Data Loader Module.

Provides functionality to stream the RoboDojo dataset from HuggingFace
in chunks to avoid loading the full dataset into RAM.
"""
import os
from typing import Iterator, Dict, Any, Optional, Generator
import logging

# Attempt to import datasets; if missing, the user must install it per requirements.txt
try:
    from datasets import load_dataset
except ImportError:
    raise ImportError(
        "The 'datasets' package is required. "
        "Please install it via: pip install datasets"
    )

from config import DATASET_COMMIT_HASH, DATASET_HF_ID

logger = logging.getLogger(__name__)

def stream_robodojo_tasks(
    split: Optional[str] = None,
    streaming: bool = True
) -> Generator[Dict[str, Any], None, None]:
    """
    Streams RoboDojo tasks from HuggingFace.
    
    Args:
        split: Optional split name (e.g., 'train', 'test'). If None, streams all.
        streaming: If True, streams data chunk-by-chunk. If False, loads into memory 
                   (not recommended for full dataset).
    
    Yields:
        A dictionary representing a single task record.
    
    Raises:
        RuntimeError: If the dataset cannot be fetched from the real source.
    """
    logger.info(f"Loading RoboDojo dataset from HuggingFace: {DATASET_HF_ID} @ {DATASET_COMMIT_HASH}")
    
    # Configure dataset loading with specific revision to ensure reproducibility
    # per spec requirement for commit hash v3.0.1 (mapped to DATASET_COMMIT_HASH in config)
    ds = load_dataset(
        DATASET_HF_ID,
        split=split,
        streaming=streaming,
        revision=DATASET_COMMIT_HASH
    )
    
    logger.info("Dataset loaded successfully. Iterating...")
    
    # Iterate over the dataset. If streaming=True, this yields one example at a time.
    # If streaming=False, this iterates over the in-memory dataset.
    for item in ds:
        yield item

def load_task_by_id(task_id: str) -> Optional[Dict[str, Any]]:
    """
    Loads a specific task by its ID.
    
    Note: This requires iterating through the stream until the ID is found.
    For large datasets, filtering by ID on the server side (if supported) 
    or using a specific split is preferred.
    
    Args:
        task_id: The unique identifier of the task.
    
    Returns:
        The task dictionary if found, None otherwise.
    """
    for task in stream_robodojo_tasks():
        # RoboDojo dataset typically uses 'task_id' or 'id' as the key. 
        # We check common variations.
        if task.get('task_id') == task_id or task.get('id') == task_id:
            return task
    return None

def get_dataset_info() -> Dict[str, Any]:
    """
    Retrieves metadata about the RoboDojo dataset.
    
    Returns:
        Dictionary containing dataset info (features, number of examples if available).
    """
    # Note: With streaming=True, len() is not available immediately without counting.
    # We load metadata without streaming to get feature info.
    ds = load_dataset(
        DATASET_HF_ID,
        revision=DATASET_COMMIT_HASH,
        streaming=False
    )
    
    # If the dataset has multiple splits, return info for the first one or a summary
    if hasattr(ds, 'keys'):
        return {
            "splits": list(ds.keys()),
            "features": ds[list(ds.keys())[0]].features if ds else None
        }
    return {
        "features": ds.features if hasattr(ds, 'features') else None
    }