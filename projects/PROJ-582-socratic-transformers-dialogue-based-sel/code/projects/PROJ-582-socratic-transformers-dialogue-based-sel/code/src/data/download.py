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


def download_dataset(
    dataset_name: str,
    split: str = "train",
    streaming: bool = True,
    max_samples: Optional[int] = None
) -> Any:
    """
    Download a dataset from HuggingFace.

    Args:
        dataset_name: The HuggingFace dataset identifier (e.g., 'gsm8k', 'competition_math')
        split: The dataset split to load (default: 'train')
        streaming: If True, stream the dataset instead of loading fully into memory
        max_samples: Optional limit on number of samples to process

    Returns:
        The loaded dataset object (Dataset or IterableDataset)

    Raises:
        ValueError: If dataset_name is invalid
        Exception: Propagates any errors from the HuggingFace datasets library
    """
    config = get_config()
    logger = config.logger

    logger.info(f"Downloading dataset: {dataset_name}, split: {split}, streaming: {streaming}")

    try:
        # Handle dataset name mapping
        if dataset_name == "gsm8k":
            ds = load_dataset(
                "gsm8k",
                "main",
                split=split,
                streaming=streaming
            )
        elif dataset_name == "math" or dataset_name == "competition_math":
            # MATH dataset on HF is often under 'competition_math'
            ds = load_dataset(
                "competition_math",
                split=split,
                streaming=streaming
            )
        else:
            raise ValueError(f"Unsupported dataset name: {dataset_name}")

        if max_samples is not None:
            # If streaming, we need to iterate and limit
            if streaming:
                from itertools import islice
                ds = islice(ds, max_samples)
            else:
                ds = ds.select(range(min(max_samples, len(ds))))

        logger.info(f"Successfully loaded dataset: {dataset_name} ({len(ds) if not streaming else 'streaming'} samples)")
        return ds

    except Exception as e:
        logger.error(f"Failed to download dataset {dataset_name}: {str(e)}")
        raise


def download_all_datasets(
    output_dir: Optional[Path] = None,
    max_samples: Optional[int] = None
) -> Dict[str, Any]:
    """
    Download all required datasets (GSM8K and MATH) and save them locally.

    Args:
        output_dir: Directory to save processed datasets. If None, uses config default.
        max_samples: Optional limit on samples per dataset

    Returns:
        Dictionary mapping dataset names to their loaded objects
    """
    config = get_config()
    logger = config.logger

    if output_dir is None:
        output_dir = config.data_dir / "processed"

    output_dir.mkdir(parents=True, exist_ok=True)

    datasets_to_download = ["gsm8k", "math"]
    downloaded_datasets = {}

    for ds_name in datasets_to_download:
        logger.info(f"Processing {ds_name}...")

        # Download with streaming to avoid memory issues
        ds = download_dataset(
            dataset_name=ds_name,
            split="train",
            streaming=True,
            max_samples=max_samples
        )

        # Save to disk in parquet format for efficient loading later
        output_path = output_dir / f"{ds_name}_train.parquet"

        # Convert to list for saving (only if not too large)
        # For large datasets, we might want to save in chunks
        try:
            # For streaming datasets, we need to materialize to save
            # We'll do this carefully to avoid OOM
            samples = []
            for i, sample in enumerate(ds):
                if max_samples and i >= max_samples:
                    break
                samples.append(sample)

            # Create a proper dataset from the list
            from datasets import Dataset
            ds_materialized = Dataset.from_list(samples)
            ds_materialized.save_to_disk(str(output_path))

            downloaded_datasets[ds_name] = ds_materialized
            logger.info(f"Saved {ds_name} to {output_path} ({len(samples)} samples)")

        except Exception as e:
            logger.error(f"Failed to save {ds_name}: {str(e)}")
            raise

    return downloaded_datasets


def main():
    """Main entry point for dataset download."""
    import argparse

    parser = argparse.ArgumentParser(description="Download datasets for Socratic Transformers project")
    parser.add_argument("--max-samples", type=int, default=None, help="Maximum samples per dataset")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory for datasets")
    args = parser.parse_args()

    # Initialize config
    config = get_config()
    logger = config.logger

    logger.info("Starting dataset download...")

    output_dir = Path(args.output_dir) if args.output_dir else None

    try:
        datasets = download_all_datasets(
            output_dir=output_dir,
            max_samples=args.max_samples
        )

        logger.info("Dataset download completed successfully!")
        for name, ds in datasets.items():
            logger.info(f"  - {name}: {len(ds)} samples")

    except Exception as e:
        logger.error(f"Dataset download failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()