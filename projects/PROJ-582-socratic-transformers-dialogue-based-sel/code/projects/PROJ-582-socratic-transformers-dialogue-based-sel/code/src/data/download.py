"""
Dataset downloader for Socratic Transformers project.
Fetches GSM8K and MATH datasets from HuggingFace.
"""
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

from datasets import load_dataset
from src.utils.config import get_config, SocraticConfig


def download_dataset(
    dataset_name: str,
    split: str = "train",
    output_dir: Optional[Path] = None,
    streaming: bool = False
) -> Any:
    """
    Download a dataset from HuggingFace.

    Args:
        dataset_name: Name of the dataset on HuggingFace (e.g., 'gsm8k', 'hendrycks/math')
        split: Dataset split to load (default: 'train')
        output_dir: Directory to cache/download the dataset (default: from config)
        streaming: If True, stream the dataset without full download (for large datasets)

    Returns:
        The loaded dataset object (Dataset or IterableDataset)

    Raises:
        ValueError: If dataset_name is invalid or download fails
        RuntimeError: If real data source is unreachable and no fallback is allowed
    """
    config: SocraticConfig = get_config()

    # Determine output directory
    if output_dir is None:
        output_dir = Path(config.data_dir) / "raw"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Map short names to HuggingFace dataset IDs
    dataset_map = {
        "gsm8k": "gsm8k",
        "math": "hendrycks/math",
        "gsm8k:main": "gsm8k:main",
    }

    if dataset_name not in dataset_map:
        raise ValueError(
            f"Unknown dataset: {dataset_name}. "
            f"Available: {list(dataset_map.keys())}"
        )

    hf_dataset_id = dataset_map[dataset_name]

    try:
        if streaming:
            # Stream dataset to avoid memory issues with large datasets
            dataset = load_dataset(
                hf_dataset_id,
                split=split,
                streaming=True,
                trust_remote_code=True
            )
        else:
            # Full download (for smaller datasets or when full access needed)
            dataset = load_dataset(
                hf_dataset_id,
                split=split,
                cache_dir=str(output_dir),
                trust_remote_code=True
            )

        return dataset

    except Exception as e:
        # Fail loudly - no synthetic fallback
        raise RuntimeError(
            f"Failed to download dataset '{dataset_name}' from HuggingFace: {e}. "
            "Check your internet connection and dataset availability. "
            "No synthetic data fallback is permitted."
        ) from e


def download_all_datasets(
    output_dir: Optional[Path] = None,
    streaming: bool = False
) -> Dict[str, Any]:
    """
    Download all required datasets for the project.

    Args:
        output_dir: Directory to store downloaded datasets
        streaming: Whether to stream datasets instead of full download

    Returns:
        Dictionary mapping dataset names to their loaded datasets
    """
    datasets_to_download = [
        ("gsm8k", "train"),
        ("gsm8k", "test"),
        ("math", "train"),
        ("math", "test"),
    ]

    downloaded = {}

    for dataset_name, split in datasets_to_download:
        print(f"Downloading {dataset_name} ({split})...")
        try:
            dataset = download_dataset(
                dataset_name=dataset_name,
                split=split,
                output_dir=output_dir,
                streaming=streaming
            )
            downloaded[f"{dataset_name}_{split}"] = dataset
            print(f"  ✓ Successfully downloaded {dataset_name}_{split}")
        except Exception as e:
            print(f"  ✗ Failed to download {dataset_name}_{split}: {e}")
            # Re-raise to fail loudly as per requirements
            raise

    return downloaded


def main():
    """
    Main entry point for dataset download script.
    Downloads GSM8K and MATH datasets to the configured data directory.
    """
    config = get_config()
    output_dir = Path(config.data_dir) / "raw"

    print("Starting dataset download for Socratic Transformers project...")
    print(f"Output directory: {output_dir}")

    try:
        datasets = download_all_datasets(output_dir=output_dir, streaming=False)

        print("\nDownload Summary:")
        for name, dataset in datasets.items():
            if hasattr(dataset, "__len__"):
                print(f"  {name}: {len(dataset)} samples")
            else:
                print(f"  {name}: streaming dataset (length unknown)")

        print("\n✓ All datasets downloaded successfully.")
        return 0

    except Exception as e:
        print(f"\n✗ Download failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())