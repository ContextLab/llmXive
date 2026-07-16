"""
Data loading utilities for eye-tracking data.

This module provides functions to fetch eye-tracking data from verified sources.
It strictly adheres to the "Verified datasets" block in plan.md:
- University of Dundee Eye-Tracking Corpus
- Boston University Eye-Tracking Dataset

The module uses the HuggingFace `datasets` library to fetch data programmatically.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

import pandas as pd
from datasets import load_dataset, Dataset

# Configure logger
logger = logging.getLogger(__name__)


def load_dundee_eye_tracking(
    split: str = "train",
    streaming: bool = False,
    revision: Optional[str] = None
) -> pd.DataFrame:
    """
    Fetch the University of Dundee Eye-Tracking Corpus from HuggingFace.

    This dataset contains eye-tracking data from participants reading sentences.
    It is a verified source per the project plan.

    Args:
        split: The dataset split to load ('train', 'test', 'validation', or None for all).
        streaming: If True, stream the dataset instead of loading into memory.
        revision: Specific revision tag (e.g., 'v1.0.0') if needed.

    Returns:
        pd.DataFrame: The eye-tracking data.

    Raises:
        ValueError: If the dataset cannot be found or loaded.
        RuntimeError: If the fetch fails and no fallback is available.
    """
    dataset_id = "nab/dundee_eye_tracking_corpus"
    logger.info(f"Attempting to load dataset: {dataset_id}")

    try:
        if streaming:
            ds = load_dataset(
                dataset_id,
                split=split if split else None,
                streaming=True,
                revision=revision
            )
            # Convert streaming dataset to DataFrame (iterative approach for memory efficiency)
            # For large datasets, we might want to process in chunks, but for now
            # we convert the first split to a DataFrame.
            if hasattr(ds, 'to_pandas'):
                df = ds.to_pandas()
            else:
                # Fallback for streaming datasets that don't have to_pandas directly
                # We assume the dataset is small enough to convert or we take a sample
                # In a real scenario, we would iterate and accumulate.
                # For this implementation, we try to convert directly.
                df = pd.DataFrame(list(ds))
        else:
            ds = load_dataset(
                dataset_id,
                split=split if split else None,
                revision=revision
            )
            if isinstance(ds, dict):
                # If multiple splits, return the requested one or the first
                if split and split in ds:
                    df = ds[split].to_pandas()
                else:
                    # Default to first split if split not specified
                    first_key = next(iter(ds))
                    df = ds[first_key].to_pandas()
            else:
                df = ds.to_pandas()

        logger.info(f"Successfully loaded {len(df)} rows from Dundee dataset.")
        return df

    except Exception as e:
        logger.error(f"Failed to load Dundee dataset: {e}")
        # Fail loudly as per requirements - no synthetic fallback
        raise RuntimeError(f"Failed to load verified eye-tracking data from {dataset_id}: {e}")


def load_boston_eye_tracking(
    split: str = "train",
    streaming: bool = False,
    revision: Optional[str] = None
) -> pd.DataFrame:
    """
    Fetch the Boston University Eye-Tracking Dataset from HuggingFace.

    This dataset contains eye-tracking data from participants reading news articles.
    It is a verified source per the project plan.

    Args:
        split: The dataset split to load.
        streaming: If True, stream the dataset.
        revision: Specific revision tag.

    Returns:
        pd.DataFrame: The eye-tracking data.

    Raises:
        ValueError: If the dataset cannot be found or loaded.
        RuntimeError: If the fetch fails.
    """
    dataset_id = "nab/boston_university_eye_tracking"
    logger.info(f"Attempting to load dataset: {dataset_id}")

    try:
        if streaming:
            ds = load_dataset(
                dataset_id,
                split=split if split else None,
                streaming=True,
                revision=revision
            )
            if hasattr(ds, 'to_pandas'):
                df = ds.to_pandas()
            else:
                df = pd.DataFrame(list(ds))
        else:
            ds = load_dataset(
                dataset_id,
                split=split if split else None,
                revision=revision
            )
            if isinstance(ds, dict):
                if split and split in ds:
                    df = ds[split].to_pandas()
                else:
                    first_key = next(iter(ds))
                    df = ds[first_key].to_pandas()
            else:
                df = ds.to_pandas()

        logger.info(f"Successfully loaded {len(df)} rows from Boston dataset.")
        return df

    except Exception as e:
        logger.error(f"Failed to load Boston dataset: {e}")
        raise RuntimeError(f"Failed to load verified eye-tracking data from {dataset_id}: {e}")


def fetch_eye_tracking_data(
    source: str = "dundee",
    split: str = "train",
    streaming: bool = False,
    revision: Optional[str] = None
) -> pd.DataFrame:
    """
    Main entry point to fetch eye-tracking data from verified sources.

    Args:
        source: The source dataset ('dundee' or 'boston').
        split: The dataset split to load.
        streaming: If True, stream the dataset.
        revision: Specific revision tag.

    Returns:
        pd.DataFrame: The eye-tracking data.

    Raises:
        ValueError: If an unknown source is specified.
        RuntimeError: If the fetch fails.
    """
    source = source.lower()
    if source == "dundee":
        return load_dundee_eye_tracking(split=split, streaming=streaming, revision=revision)
    elif source == "boston":
        return load_boston_eye_tracking(split=split, streaming=streaming, revision=revision)
    else:
        raise ValueError(f"Unknown eye-tracking source: {source}. Use 'dundee' or 'boston'.")


def validate_eye_tracking_schema(df: pd.DataFrame) -> bool:
    """
    Validate that the loaded DataFrame has the expected schema for eye-tracking data.

    Expected columns (at minimum):
    - participant_id
    - trial_id
    - timestamp
    - x (gaze x-coordinate)
    - y (gaze y-coordinate)

    Args:
        df: The DataFrame to validate.

    Returns:
        bool: True if schema is valid, False otherwise.
    """
    required_columns = {'participant_id', 'trial_id', 'timestamp', 'x', 'y'}
    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        logger.warning(f"Missing required columns: {missing}")
        return False
    return True


def main():
    """
    Main function to demonstrate data loading.
    This function attempts to load data from the Dundee dataset.
    """
    # Setup logging
    logging.basicConfig(level=logging.INFO)

    try:
        # Attempt to load data
        logger.info("Starting data loading process...")
        df = fetch_eye_tracking_data(source="dundee", split="train")
        
        # Validate schema
        if validate_eye_tracking_schema(df):
            logger.info("Schema validation passed.")
            logger.info(f"Dataset shape: {df.shape}")
            logger.info(f"Columns: {list(df.columns)}")
            logger.info(f"First few rows:\n{df.head()}")
        else:
            logger.error("Schema validation failed.")
            
    except Exception as e:
        logger.error(f"Data loading failed: {e}")
        raise


if __name__ == "__main__":
    main()
