"""
Data loading utilities for HuggingFace datasets.
Implements streaming to handle large datasets without memory exhaustion.
"""
import logging
from typing import Optional, Dict, Any, List, Generator
from pathlib import Path
import json
import os
from code.src.config import Config

try:
    from datasets import load_dataset
except ImportError:
    raise ImportError("The 'datasets' package is required. Install it with: pip install datasets")

logger = logging.getLogger(__name__)

def load_dag_sft_dataset(
    name: Optional[str] = None,
    split: Optional[str] = None,
    streaming: bool = True
):
    """
    Load the DAG SFT dataset from HuggingFace.
    
    Args:
        name: Dataset name (defaults to config).
        split: Dataset split (defaults to config).
        streaming: If True, stream the dataset instead of loading into memory.
        
    Returns:
        Dataset object (streaming or loaded).
        
    Raises:
        FileNotFoundError: If the dataset cannot be found.
        ConnectionError: If the network request fails.
    """
    config = Config()
    dataset_name = name or config.get_dataset_name()
    dataset_split = split or config.get("dataset.split", "train")
    
    logger.info(f"Loading dataset: {dataset_name} (split={dataset_split}, streaming={streaming})")
    
    try:
        ds = load_dataset(
            dataset_name,
            split=dataset_split,
            streaming=streaming
        )
        return ds
    except Exception as e:
        # Fail loudly: do not fall back to synthetic data
        error_msg = f"Failed to load dataset {dataset_name}: {e}"
        logger.error(error_msg)
        # Re-raise to ensure the failure is visible
        raise ConnectionError(error_msg) from e

def get_dataset_info(name: Optional[str] = None) -> Dict[str, Any]:
    """
    Get basic information about the dataset.
    """
    config = Config()
    dataset_name = name or config.get_dataset_name()
    
    try:
        # Load a small sample to get info
        ds = load_dataset(dataset_name, split="train", streaming=True)
        # Get features
        features = ds.features
        return {
            "name": dataset_name,
            "features": str(features),
            "num_columns": len(features) if features else 0
        }
    except Exception as e:
        logger.error(f"Failed to get dataset info: {e}")
        return {"error": str(e)}

def iterate_dataset_examples(
    name: Optional[str] = None,
    split: Optional[str] = None,
    max_examples: Optional[int] = None
) -> Generator[Dict[str, Any], None, None]:
    """
    Iterate over dataset examples in a streaming fashion.
    
    Args:
        name: Dataset name.
        split: Dataset split.
        max_examples: Maximum number of examples to yield.
        
    Yields:
        Dictionary representing each example.
    """
    ds = load_dag_sft_dataset(name, split, streaming=True)
    count = 0
    for example in ds:
        yield example
        count += 1
        if max_examples and count >= max_examples:
            break

def save_dataset_to_parquet(ds, output_path: Path) -> None:
    """
    Save a dataset to Parquet format.
    """
    # Convert streaming dataset to list if necessary, or use to_parquet if available
    # For streaming, we might need to iterate and save in chunks
    logger.info(f"Saving dataset to {output_path}")
    # Placeholder for actual implementation if needed
    # In a real scenario, we would use ds.to_parquet() if not streaming
    # For streaming, we would iterate and write manually
    raise NotImplementedError("Parquet saving for streaming datasets requires chunked implementation.")

def load_dataset_from_parquet(path: Path) -> Any:
    """
    Load a dataset from Parquet format.
    """
    raise NotImplementedError("Loading from Parquet is not implemented yet.")
