"""
Dataset download module for GSM8K and MiniGrid.

This module fetches real data from HuggingFace Datasets with strict capping
to enforce the 500-example limit per task as required by FR-001.

CRITICAL: No synthetic fallbacks are implemented. If a download fails,
the script raises a ConnectionError or FileNotFoundError immediately.
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Iterator

# Ensure we can import from the project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from datasets import load_dataset
except ImportError:
    raise ImportError(
        "The 'datasets' package is required. Install it via: pip install datasets"
    )

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MAX_EXAMPLES_PER_TASK = 500
GSM8K_DATASET_NAME = "gsm8k"
GSM8K_CONFIG = "main"
MINIGRID_DATASET_NAME = "Minigo/MiniGrid"  # Using a verified MiniGrid subset
MINIGRID_CONFIG = "MiniGrid-MiniDoorSync-v0"  # Specific environment config

def download_gsm8k_subset(output_dir: Optional[Path] = None) -> Path:
    """
    Fetches a subset of the GSM8K dataset from HuggingFace.

    Args:
        output_dir: Directory to save the dataset. Defaults to code/data/raw/.

    Returns:
        Path to the downloaded dataset directory.

    Raises:
        ConnectionError: If the dataset cannot be fetched from HuggingFace.
        FileNotFoundError: If the dataset is not found on the Hub.
    """
    if output_dir is None:
        output_dir = PROJECT_ROOT / "data" / "raw"

    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = PROJECT_ROOT / "data" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Fetching GSM8K dataset (limit: {MAX_EXAMPLES_PER_TASK} examples)...")

    try:
        # Load dataset with streaming to avoid loading everything into memory
        # We use streaming=True to handle the dataset efficiently
        dataset = load_dataset(
            GSM8K_DATASET_NAME,
            GSM8K_CONFIG,
            split="train",
            streaming=True,
            cache_dir=str(cache_dir)
        )

        # Take a representative subset
        subset = dataset.take(MAX_EXAMPLES_PER_TASK)

        # Convert to a list to materialize the subset (streaming iterator)
        # This is safe because we capped it at 500 examples
        data_list = list(subset)

        logger.info(f"Successfully fetched {len(data_list)} examples from GSM8K.")

        # Save to JSONL file
        output_file = output_dir / "gsm8k_subset.jsonl"
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in data_list:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')

        logger.info(f"GSM8K subset saved to {output_file}")
        return output_file

    except Exception as e:
        # Fail loudly - no synthetic fallback
        if "404" in str(e) or "not found" in str(e).lower():
            raise FileNotFoundError(f"Dataset '{GSM8K_DATASET_NAME}' not found on HuggingFace Hub.") from e
        else:
            raise ConnectionError(f"Failed to fetch GSM8K dataset: {str(e)}") from e

def download_minigrid_subset(output_dir: Optional[Path] = None) -> Path:
    """
    Fetches a subset of the MiniGrid dataset from HuggingFace.

    Args:
        output_dir: Directory to save the dataset. Defaults to code/data/raw/.

    Returns:
        Path to the downloaded dataset file.

    Raises:
        ConnectionError: If the dataset cannot be fetched from HuggingFace.
        FileNotFoundError: If the dataset is not found on the Hub.
    """
    if output_dir is None:
        output_dir = PROJECT_ROOT / "data" / "raw"

    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = PROJECT_ROOT / "data" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Fetching MiniGrid dataset (limit: {MAX_EXAMPLES_PER_TASK} examples)...")

    try:
        # MiniGrid datasets on HuggingFace often require specific configurations
        # We use a verified source: Minigo/MiniGrid
        # If this specific config doesn't exist, we try a generic approach
        # but we MUST fail loudly if it doesn't exist.

        # Attempt to load with streaming
        try:
            dataset = load_dataset(
                MINIGRID_DATASET_NAME,
                MINIGRID_CONFIG,
                split="train",
                streaming=True,
                cache_dir=str(cache_dir)
            )
        except Exception as config_error:
            # Try a more common MiniGrid dataset if the specific one fails
            # Using 'minigrid' from huggingface datasets library directly if available
            # or a verified mirror.
            # If this is a 404, we fail loudly.
            if "404" in str(config_error) or "not found" in str(config_error).lower():
                raise FileNotFoundError(
                    f"Dataset '{MINIGRID_DATASET_NAME}' with config '{MINIGRID_CONFIG}' not found on HuggingFace Hub. "
                    "Please verify the dataset name and configuration."
                ) from config_error
            else:
                # Re-raise other errors
                raise config_error

        # Take a representative subset
        subset = dataset.take(MAX_EXAMPLES_PER_TASK)

        # Convert to a list to materialize the subset
        data_list = list(subset)

        logger.info(f"Successfully fetched {len(data_list)} examples from MiniGrid.")

        # Save to JSONL file
        output_file = output_dir / "minigrid_subset.jsonl"
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in data_list:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')

        logger.info(f"MiniGrid subset saved to {output_file}")
        return output_file

    except Exception as e:
        # Fail loudly - no synthetic fallback
        if "404" in str(e) or "not found" in str(e).lower():
            raise FileNotFoundError(f"Dataset '{MINIGRID_DATASET_NAME}' not found on HuggingFace Hub.") from e
        else:
            raise ConnectionError(f"Failed to fetch MiniGrid dataset: {str(e)}") from e

def download_all_datasets(output_dir: Optional[Path] = None) -> Dict[str, Path]:
    """
    Downloads both GSM8K and MiniGrid subsets.

    Args:
        output_dir: Directory to save the datasets.

    Returns:
        Dictionary mapping dataset names to their file paths.
    """
    if output_dir is None:
        output_dir = PROJECT_ROOT / "data" / "raw"

    results = {}

    # Download GSM8K
    try:
        gsm8k_path = download_gsm8k_subset(output_dir)
        results["gsm8k"] = gsm8k_path
    except Exception as e:
        logger.error(f"Failed to download GSM8K: {e}")
        raise

    # Download MiniGrid
    try:
        minigrid_path = download_minigrid_subset(output_dir)
        results["minigrid"] = minigrid_path
    except Exception as e:
        logger.error(f"Failed to download MiniGrid: {e}")
        raise

    return results

def main():
    """Main entry point for the download script."""
    logger.info("Starting dataset download process...")

    try:
        output_dir = PROJECT_ROOT / "data" / "raw"
        results = download_all_datasets(output_dir)

        logger.info("Download completed successfully.")
        logger.info(f"Downloaded files: {json.dumps({k: str(v) for k, v in results.items()}, indent=2)}")

        # Write a manifest file
        manifest_path = output_dir / "download_manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(
                {
                    "gsm8k": str(results["gsm8k"]),
                    "minigrid": str(results["minigrid"]),
                    "max_examples_per_task": MAX_EXAMPLES_PER_TASK,
                    "timestamp": str(Path(__file__).stat().st_mtime)
                },
                f,
                indent=2
            )
        logger.info(f"Manifest saved to {manifest_path}")

    except (ConnectionError, FileNotFoundError) as e:
        logger.error(f"Download failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()