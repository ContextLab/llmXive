"""
Dataset downloader for GSM8K and MATH datasets.
Fetches real data from HuggingFace datasets.
"""
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

from datasets import load_dataset
from src.utils.config import get_config, SocraticConfig


def ensure_data_dirs(base_path: Optional[Path] = None) -> Dict[str, Path]:
    """
    Ensure required data directories exist.
    Returns a dictionary of directory paths.
    """
    if base_path is None:
        # Default to project root's data directory
        base_path = Path(__file__).parent.parent.parent.parent / "data"

    dirs = {
        "raw": base_path / "raw",
        "processed": base_path / "processed",
        "results": base_path / "results",
    }

    for dir_path in dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)

    return dirs


def download_dataset(
    dataset_name: str,
    split: str = "train",
    subset: Optional[str] = None,
    streaming: bool = False,
    output_dir: Optional[Path] = None,
) -> Any:
    """
    Download a dataset from HuggingFace.

    Args:
        dataset_name: Name of the dataset (e.g., 'gsm8k', 'competition_math')
        split: Dataset split to load (e.g., 'train', 'test')
        subset: Subset name if applicable (e.g., 'main' for gsm8k)
        streaming: If True, stream the dataset instead of loading entirely
        output_dir: Directory to cache/save the dataset

    Returns:
        The loaded dataset object

    Raises:
        ValueError: If dataset cannot be found or loaded
        RuntimeError: If download fails
    """
    config = get_config()

    # Map dataset names to HuggingFace identifiers
    dataset_map = {
        "gsm8k": {"name": "gsm8k", "subset": subset or "main"},
        "math": {"name": "competition_math", "subset": subset or "train"},
    }

    if dataset_name not in dataset_map:
        raise ValueError(f"Unsupported dataset: {dataset_name}. Supported: {list(dataset_map.keys())}")

    hf_config = dataset_map[dataset_name]

    try:
        if streaming:
            # Stream the dataset to avoid memory issues
            dataset = load_dataset(
                hf_config["name"],
                hf_config["subset"],
                split=split,
                streaming=True,
                trust_remote_code=True,
            )
        else:
            # Load entire dataset into memory
            dataset = load_dataset(
                hf_config["name"],
                hf_config["subset"],
                split=split,
                trust_remote_code=True,
            )

        # Save to disk if output_dir is specified
        if output_dir:
            output_path = output_dir / f"{dataset_name}_{split}"
            output_path.mkdir(parents=True, exist_ok=True)
            # For streaming datasets, we iterate and save manually
            # For regular datasets, use save_to_disk
            if streaming:
                # Convert streaming dataset to regular for saving
                dataset = dataset.map(lambda x: x)  # Force materialization
            dataset.save_to_disk(str(output_path))

        return dataset

    except Exception as e:
        raise RuntimeError(f"Failed to download dataset {dataset_name}: {str(e)}") from e


def download_all_datasets(
    output_dir: Optional[Path] = None,
    splits: Optional[List[str]] = None,
    streaming: bool = False,
) -> Dict[str, Any]:
    """
    Download all required datasets (GSM8K and MATH).

    Args:
        output_dir: Base directory to save datasets
        splits: List of splits to download (default: ['train', 'test'])
        streaming: Whether to stream datasets

    Returns:
        Dictionary mapping dataset names to loaded dataset objects
    """
    if splits is None:
        splits = ["train", "test"]

    if output_dir is None:
        dirs = ensure_data_dirs()
        output_dir = dirs["raw"]

    datasets = {}

    # Download GSM8K
    print("Downloading GSM8K dataset...")
    for split in splits:
        try:
            dataset = download_dataset(
                "gsm8k",
                split=split,
                subset="main",
                streaming=streaming,
                output_dir=output_dir,
            )
            datasets[f"gsm8k_{split}"] = dataset
            print(f"  GSM8K {split} split downloaded successfully.")
        except Exception as e:
            print(f"  Warning: Failed to download GSM8K {split}: {e}")

    # Download MATH
    print("Downloading MATH dataset...")
    for split in splits:
        try:
            dataset = download_dataset(
                "math",
                split=split,
                subset="train" if split == "train" else "test",
                streaming=streaming,
                output_dir=output_dir,
            )
            datasets[f"math_{split}"] = dataset
            print(f"  MATH {split} split downloaded successfully.")
        except Exception as e:
            print(f"  Warning: Failed to download MATH {split}: {e}")

    return datasets


def main() -> None:
    """
    Main entry point for downloading datasets.
    """
    print("Starting dataset download for Socratic Transformers project...")

    # Ensure data directories exist
    dirs = ensure_data_dirs()
    print(f"Data directories created at: {dirs['raw']}")

    # Download datasets
    datasets = download_all_datasets(output_dir=dirs["raw"], streaming=False)

    # Report results
    print("\nDownload Summary:")
    for name, dataset in datasets.items():
        if hasattr(dataset, "__len__"):
            print(f"  {name}: {len(dataset)} samples")
        else:
            print(f"  {name}: streaming dataset")

    print("\nDataset download complete.")


if __name__ == "__main__":
    main()
