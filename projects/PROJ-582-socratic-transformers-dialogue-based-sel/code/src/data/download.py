import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

from datasets import load_dataset
from src.utils.config import get_config, SocraticConfig
from src.utils.logging import get_logger

# Initialize logger for this module
logger = get_logger(__name__)

def download_dataset(
    dataset_name: str,
    split: str = "train",
    cache_dir: Optional[str] = None,
    streaming: bool = False
) -> Any:
    """
    Download a dataset from Hugging Face Hub.

    This function fetches real data from the Hugging Face datasets library.
    It does NOT generate synthetic data or fall back to mock data.
    If the dataset is unavailable, it will raise an exception (fail loudly).

    Args:
        dataset_name (str): The HuggingFace dataset identifier (e.g., "gsm8k").
        split (str): The dataset split to load (e.g., "train", "test").
        cache_dir (str, optional): Directory to cache the dataset.
        streaming (bool): If True, stream the dataset instead of loading fully into memory.

    Returns:
        The loaded dataset (Dataset or DatasetDict).

    Raises:
        Exception: If the dataset cannot be fetched from the real source.
    """
    logger.info(f"Attempting to download dataset: {dataset_name} (split: {split}, streaming: {streaming})")

    try:
        dataset = load_dataset(
            dataset_name,
            split=split,
            cache_dir=cache_dir,
            streaming=streaming
        )
        logger.info(f"Successfully loaded dataset: {dataset_name}")
        return dataset
    except Exception as e:
        logger.error(f"Failed to download dataset {dataset_name}: {e}")
        # Fail loudly as per constraints: do not catch and return synthetic data
        raise e


def download_all_datasets(
    output_dir: Optional[str] = None,
    cache_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Download all required datasets for the Socratic Transformers project.

    Currently downloads:
    - GSM8K (Grade School Math 8K)
    - MATH (MATH dataset for competition mathematics)

    Args:
        output_dir (str, optional): Directory to save processed datasets (not used for raw download here,
                                    but used to log where they should go).
        cache_dir (str, optional): Directory to cache HuggingFace datasets.

    Returns:
        Dict[str, Any]: A dictionary mapping dataset names to their loaded datasets.
    """
    config: SocraticConfig = get_config()
    if cache_dir is None:
        cache_dir = str(config.data_dir / "raw" / ".cache")

    datasets_to_download = [
        "gsm8k",
        "math_dataset"  # Using 'math_dataset' as the HF ID for MATH
    ]

    downloaded_data = {}

    for ds_name in datasets_to_download:
        try:
            # GSM8K has a 'train' and 'test' split. We fetch train for generation.
            # MATH has 'train' and 'test'.
            if ds_name == "gsm8k":
                # GSM8K is often loaded with a config 'main' or just default
                ds = download_dataset(ds_name, split="train", cache_dir=cache_dir)
                downloaded_data[ds_name] = ds
            elif ds_name == "math_dataset":
                # MATH dataset
                ds = download_dataset(ds_name, split="train", cache_dir=cache_dir)
                downloaded_data[ds_name] = ds
            else:
                logger.warning(f"Unknown dataset {ds_name}, skipping.")

        except Exception as e:
            logger.error(f"Critical failure downloading {ds_name}: {e}")
            # Re-raise to ensure the pipeline fails loudly if a required dataset is missing
            raise e

    logger.info(f"All datasets downloaded successfully. Count: {len(downloaded_data)}")
    return downloaded_data


def main():
    """
    Main entry point for the dataset downloader script.
    Downloads GSM8K and MATH datasets to the configured cache directory.
    """
    logger.info("Starting dataset download process for Socratic Transformers project.")

    config = get_config()
    # Ensure raw data directory exists
    raw_dir = config.data_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    try:
        datasets = download_all_datasets(cache_dir=str(raw_dir))
        logger.info(f"Downloaded datasets keys: {list(datasets.keys())}")

        # Log basic info about the datasets
        for name, ds in datasets.items():
            logger.info(f"Dataset '{name}' loaded. Type: {type(ds)}")
            # If it's a DatasetDict (common for some HF datasets), inspect splits
            if hasattr(ds, 'keys'):
                logger.info(f"  Splits available: {list(ds.keys())}")
            elif hasattr(ds, 'num_rows'):
                logger.info(f"  Number of rows: {ds.num_rows}")

        logger.info("Dataset download completed successfully.")

    except Exception as e:
        logger.critical(f"Dataset download failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
