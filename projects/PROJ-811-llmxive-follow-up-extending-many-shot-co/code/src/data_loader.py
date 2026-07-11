import logging
from typing import Optional, Dict, Any, List, Generator
from pathlib import Path
import json
import os

try:
    from datasets import load_dataset, DatasetDict
except ImportError:
    raise ImportError(
        "The 'datasets' package is required. Install it via: pip install datasets"
    )

from code.src.config import Config

logger = logging.getLogger(__name__)


def load_dag_sft_dataset(
    split: str = "train",
    streaming: bool = False,
    cache_dir: Optional[str] = None,
    config_name: Optional[str] = None
) -> Any:
    """
    Loads the 'aaabiao/DAG_sft' dataset from HuggingFace.

    Args:
        split: The dataset split to load (e.g., 'train', 'test', 'validation').
        streaming: If True, streams the dataset instead of downloading it fully.
        cache_dir: Optional directory to cache the dataset.
        config_name: Optional configuration name if the dataset has multiple configs.

    Returns:
        The loaded dataset object (Dataset or IterableDataset).

    Raises:
        ValueError: If the dataset or split is not found.
        RuntimeError: If the dataset cannot be loaded.
    """
    dataset_name = "aaabiao/DAG_sft"
    logger.info(f"Attempting to load dataset: {dataset_name} (split={split}, streaming={streaming})")

    try:
        if config_name:
            ds = load_dataset(
                dataset_name,
                config_name,
                split=split,
                streaming=streaming,
                cache_dir=cache_dir
            )
        else:
            ds = load_dataset(
                dataset_name,
                split=split,
                streaming=streaming,
                cache_dir=cache_dir
            )
        
        logger.info(f"Successfully loaded dataset split '{split}'.")
        return ds

    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_name}: {e}")
        raise RuntimeError(f"Could not load dataset {dataset_name}. Ensure the dataset exists and is accessible.") from e


def get_dataset_info(dataset: Any) -> Dict[str, Any]:
    """
    Retrieves metadata information about the loaded dataset.

    Args:
        dataset: The loaded dataset object.

    Returns:
        A dictionary containing dataset info (features, num_rows if available, etc.).
    """
    info = {
        "type": type(dataset).__name__,
        "features": dataset.features if hasattr(dataset, 'features') else "N/A",
    }

    if hasattr(dataset, '_indices') and hasattr(dataset, 'num_rows'):
        info["num_rows"] = dataset.num_rows
    elif hasattr(dataset, 'num_rows'):
        info["num_rows"] = dataset.num_rows
    
    logger.info(f"Dataset info: {info}")
    return info


def iterate_dataset_examples(
    dataset: Any,
    max_examples: Optional[int] = None
) -> Generator[Dict[str, Any], None, None]:
    """
    Iterates over examples in the dataset, optionally limiting the count.

    Args:
        dataset: The loaded dataset object.
        max_examples: Maximum number of examples to yield. If None, yields all.

    Yields:
        Dictionary representing a single dataset example.
    """
    count = 0
    for example in dataset:
        yield example
        count += 1
        if max_examples and count >= max_examples:
            break


def save_dataset_to_parquet(
    dataset: Any,
    output_path: str,
    split: str = "train"
) -> Path:
    """
    Saves the dataset to a Parquet file.

    Args:
        dataset: The dataset to save.
        output_path: The path (directory or file) where the parquet file will be saved.
        split: The split name to use in the filename if saving to a directory.

    Returns:
        The path to the created Parquet file.
    """
    output_path_obj = Path(output_path)
    
    # Ensure parent directory exists
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    if output_path_obj.is_dir():
        file_path = output_path_obj / f"{split}.parquet"
    else:
        file_path = output_path_obj

    logger.info(f"Saving dataset to {file_path}")
    
    if hasattr(dataset, 'to_parquet'):
        dataset.to_parquet(str(file_path))
    else:
        # Fallback for streaming or non-standard dataset objects
        # Convert to list first if possible, or raise error
        if hasattr(dataset, 'to_list'):
            data_list = list(dataset)
            import pandas as pd
            df = pd.DataFrame(data_list)
            df.to_parquet(str(file_path))
        else:
            raise NotImplementedError(
                "The provided dataset object does not support direct Parquet export "
                "and cannot be converted to a list. Please load with streaming=False."
            )

    logger.info(f"Dataset saved to {file_path}")
    return file_path


def load_dataset_from_parquet(
    input_path: str
) -> Any:
    """
    Loads a dataset from a Parquet file.

    Args:
        input_path: Path to the Parquet file.

    Returns:
        A HuggingFace Dataset object.
    """
    from datasets import Dataset
    import pandas as pd

    logger.info(f"Loading dataset from {input_path}")
    
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Parquet file not found: {input_path}")

    df = pd.read_parquet(input_path)
    ds = Dataset.from_pandas(df)
    
    logger.info(f"Loaded {len(ds)} examples from {input_path}")
    return ds
