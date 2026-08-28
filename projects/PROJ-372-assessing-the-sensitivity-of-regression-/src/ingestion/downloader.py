"""
Dataset Downloader Module.

Fetches datasets from verified sources (HuggingFace, UCI) using streaming
to handle large datasets efficiently. Implements strict failure-on-error
behavior with no synthetic fallbacks.
"""
import os
import hashlib
import logging
from typing import Optional, Dict, Any, Generator
from pathlib import Path

import pandas as pd
from datasets import load_dataset
from datasets.exceptions import DatasetNotFoundError, HfHubHTTPError

from ..utils.config import DATASET_REGISTRY
from ..utils.logger import get_logger
from ..utils.validation import validate_checksum

logger = get_logger(__name__)


def fetch_dataset(
    dataset_name: str,
    config_name: Optional[str] = None,
    split: str = "train",
    streaming: bool = True,
    cache_dir: Optional[str] = None,
) -> Generator[Dict[str, Any], None, None]:
    """
    Fetch a dataset from a verified source using streaming.

    Args:
        dataset_name: The name of the dataset as registered in DATASET_REGISTRY
                      or a valid HuggingFace dataset ID.
        config_name: Optional configuration name for HuggingFace datasets.
        split: The dataset split to load (default: 'train').
        streaming: If True, streams data in chunks. If False, loads fully into memory.
        cache_dir: Optional directory to cache the dataset.

    Returns:
        A generator yielding rows as dictionaries (if streaming) or an iterator.

    Raises:
        ValueError: If the dataset is not found in the registry or is invalid.
        Exception: Propagates any download/fetch errors (NO synthetic fallback).
    """
    logger.info(f"Fetching dataset: {dataset_name} (streaming={streaming})")

    # Check if dataset is in our verified registry
    if dataset_name in DATASET_REGISTRY:
        ds_config = DATASET_REGISTRY[dataset_name]
        hf_id = ds_config.get("hf_id")
        hf_config = ds_config.get("config")
        expected_checksum = ds_config.get("checksum")

        if not hf_id:
            raise ValueError(f"Dataset {dataset_name} has no HuggingFace ID in registry.")

        # Use config from registry if not provided
        if config_name is None:
            config_name = hf_config

        logger.info(f"Using registry config: {dataset_name} -> {hf_id} ({config_name})")
    else:
        # Allow direct HF IDs if not in registry, but warn
        logger.warning(f"Dataset {dataset_name} not in registry. Attempting direct load.")
        expected_checksum = None

    try:
        # Load dataset
        ds = load_dataset(
            hf_id if dataset_name not in DATASET_REGISTRY else DATASET_REGISTRY[dataset_name]["hf_id"],
            config=config_name if dataset_name in DATASET_REGISTRY else config_name,
            split=split,
            streaming=streaming,
            cache_dir=cache_dir,
        )

        if streaming:
            # Return generator directly
            return ds

        else:
            # Convert to pandas for memory-safe processing if not streaming
            # Note: This assumes the dataset fits in memory if streaming=False
            df = ds.to_pandas()
            logger.info(f"Loaded dataset into memory: {len(df)} rows")
            return df

    except (DatasetNotFoundError, HfHubHTTPError) as e:
        logger.error(f"Failed to fetch dataset {dataset_name}: {e}")
        # Fail loudly - no synthetic fallback
        raise RuntimeError(f"Data fetch failed for {dataset_name}: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error fetching {dataset_name}: {e}")
        raise


def ingest_and_profile(
    dataset_name: str,
    output_path: str,
    config_name: Optional[str] = None,
    split: str = "train",
) -> Dict[str, Any]:
    """
    Ingest a dataset, perform initial profiling, and save results.

    This function orchestrates the download and basic validation, then
    delegates detailed statistical profiling to the profiler module.

    Args:
        dataset_name: Name of the dataset to ingest.
        output_path: Path to save the profile JSON.
        config_name: Optional config for HuggingFace datasets.
        split: Dataset split to use.

    Returns:
        Dictionary containing the dataset profile.
    """
    logger.info(f"Starting ingestion and profiling for: {dataset_name}")

    # Fetch data (streaming by default for large datasets)
    data_source = fetch_dataset(
        dataset_name,
        config_name=config_name,
        split=split,
        streaming=True,
    )

    # Convert streaming data to a manageable format for profiling
    # For very large datasets, we might need to sample or stream into profiler
    # For now, we collect a representative sample or full data if small
    df = None
    if hasattr(data_source, "to_pandas"):
        df = data_source.to_pandas()
    else:
        # Streaming iterator - convert to DF (be careful with memory)
        # In a real scenario, we might want to stream this into the profiler
        # or take a fixed sample for initial profiling
        try:
            df = pd.DataFrame(list(data_source))
        except MemoryError:
            logger.warning("Dataset too large for memory. Taking 100k row sample.")
            data_source = fetch_dataset(
                dataset_name,
                config_name=config_name,
                split=split,
                streaming=True,
            )
            df = pd.DataFrame(list(data_source).copy()[:100000])

    if df is None or df.empty:
        raise ValueError("No data loaded for profiling.")

    # Basic validation
    if df.empty:
        raise ValueError("Dataset is empty after loading.")

    # Ensure numeric columns exist for regression analysis
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if len(numeric_cols) < 2:
        logger.warning(f"Dataset {dataset_name} has insufficient numeric columns for regression.")

    # Compute profile (delegated to profiler module)
    from .profiler import compute_profile
    profile = compute_profile(df, dataset_name)

    # Save profile to output path
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    import json
    with open(output_path, "w") as f:
        json.dump(profile, f, indent=2, default=str)

    logger.info(f"Profile saved to {output_path}")
    return profile