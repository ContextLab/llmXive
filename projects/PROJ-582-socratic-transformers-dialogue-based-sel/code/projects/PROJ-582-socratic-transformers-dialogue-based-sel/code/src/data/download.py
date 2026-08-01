"""
Dataset Downloader for Socratic Transformers Project.

This module handles the retrieval of real datasets (GSM8K, MATH) from HuggingFace
datasets, ensuring no synthetic fallbacks are used. It adheres to the project's
constraint of using real, programmatically accessible data sources.
"""
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

from datasets import load_dataset
from src.utils.config import get_config, SocraticConfig


def ensure_data_dirs() -> Path:
    """
    Ensures the data/raw directory exists and returns its path.
    """
    config = get_config()
    base_dir = config.data_dir
    raw_dir = base_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    return raw_dir


def download_dataset(
    dataset_name: str,
    subset: Optional[str] = None,
    split: str = "train",
    streaming: bool = False,
    max_samples: Optional[int] = None
) -> Any:
    """
    Downloads a dataset from HuggingFace.

    Args:
        dataset_name: The HuggingFace dataset ID (e.g., 'gsm8k', 'hendrycks/math').
        subset: The dataset configuration/revision (e.g., 'main' for gsm8k).
        split: The dataset split to load (e.g., 'train', 'test').
        streaming: If True, streams the dataset instead of loading into memory.
        max_samples: If provided, limits the dataset to the first N samples.

    Returns:
        The loaded Dataset or DatasetDict object.

    Raises:
        RuntimeError: If the dataset cannot be found or downloaded.
        ValueError: If the dataset configuration is invalid.
    """
    raw_dir = ensure_data_dirs()
    print(f"Loading dataset: {dataset_name} (subset: {subset}, split: {split})")

    try:
        if streaming:
            dataset = load_dataset(
                dataset_name,
                name=subset,
                split=split,
                streaming=True
            )
        else:
            dataset = load_dataset(
                dataset_name,
                name=subset,
                split=split
            )

        # If max_samples is specified, slice the dataset
        # Note: For streaming datasets, we must iterate and collect or use islice
        if max_samples and not streaming:
            if isinstance(dataset, dict):
                # If it's a dict of splits, apply to the requested split
                if split in dataset:
                    dataset[split] = dataset[split].select(range(min(max_samples, len(dataset[split]))))
            else:
                dataset = dataset.select(range(min(max_samples, len(dataset))))
        elif max_samples and streaming:
            # For streaming, we return an iterator wrapper logic handled by the caller
            # or we convert to a list if memory permits (not recommended for large datasets)
            # Here we return the dataset object; the caller must handle iteration limits
            # if strict memory constraints exist during iteration.
            pass

        print(f"Successfully loaded {dataset_name}")
        return dataset

    except Exception as e:
        # Fail loudly as per constraints: no synthetic fallback
        raise RuntimeError(f"Failed to download dataset '{dataset_name}': {str(e)}") from e


def download_all_datasets(
    datasets_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Downloads all configured datasets for the Socratic project.

    Defaults to GSM8K and MATH if no config is provided.

    Args:
        datasets_config: Optional dict of dataset configurations.

    Returns:
        A dictionary mapping dataset names to their loaded objects.
    """
    config = get_config()
    # Default configuration if not provided
    if datasets_config is None:
        datasets_config = {
            "gsm8k": {
                "name": "gsm8k",
                "subset": "main",
                "split": "train",
                "streaming": False,
                "max_samples": config.max_samples_per_dataset if hasattr(config, 'max_samples_per_dataset') else None
            },
            "math": {
                "name": "hendrycks/math",
                "subset": "train",
                "split": "train",
                "streaming": False,
                "max_samples": config.max_samples_per_dataset if hasattr(config, 'max_samples_per_dataset') else None
            }
        }

    loaded_datasets = {}

    for key, cfg in datasets_config.items():
        try:
            ds = download_dataset(
                dataset_name=cfg["name"],
                subset=cfg.get("subset"),
                split=cfg.get("split", "train"),
                streaming=cfg.get("streaming", False),
                max_samples=cfg.get("max_samples")
            )
            loaded_datasets[key] = ds
        except Exception as e:
            print(f"Error downloading {key}: {e}", file=sys.stderr)
            # We do not skip; if a required dataset fails, the pipeline should stop
            # unless the config explicitly marks it as optional (not implemented here)
            raise

    return loaded_datasets


def main():
    """
    Main entry point for downloading datasets.
    """
    print("Starting dataset download process...")
    try:
        datasets = download_all_datasets()
        print("All datasets downloaded successfully.")
        for name, ds in datasets.items():
            print(f"  - {name}: {ds}")
    except RuntimeError as e:
        print(f"Dataset download failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
