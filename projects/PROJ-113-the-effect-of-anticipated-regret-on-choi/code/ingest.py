"""
Data ingestion utilities for the llmXive automated science pipeline.
Handles loading data from various sources, checksumming, and HuggingFace datasets.
"""

import hashlib
import json
import os
import requests
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Try to import datasets, but handle the case where it might not be installed yet
try:
    from datasets import load_dataset
    DATASETS_AVAILABLE = True
except ImportError:
    DATASETS_AVAILABLE = False
    logging.warning("datasets library not available. Install with 'pip install datasets'")

from config import get_dataset_url, get_path, ensure_paths_exist, get_config

# Setup logger
logger = logging.getLogger(__name__)


def load_and_checksum(url: str, output_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Download a file from a URL, calculate its SHA-256 checksum, and save it.

    Args:
        url: The URL to download from.
        output_path: Optional path to save the file. If None, uses config defaults.

    Returns:
        Dictionary containing 'url', 'checksum', and 'output_path'.
    """
    logger.info(f"Downloading and checksumming: {url}")

    if output_path is None:
        output_path = get_path("data/raw", "dataset_source")

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Download file
    response = requests.get(url, stream=True)
    response.raise_for_status()

    # Calculate checksum while saving
    sha256_hash = hashlib.sha256()
    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                sha256_hash.update(chunk)
                f.write(chunk)

    checksum = sha256_hash.hexdigest()

    # Save checksums to JSON
    checksums_file = get_path("data/raw", "checksums.json")
    checksums_file.parent.mkdir(parents=True, exist_ok=True)

    checksums_data = {}
    if checksums_file.exists():
        with open(checksums_file, "r") as f:
            checksums_data = json.load(f)

    checksums_data[url] = {
        "checksum": checksum,
        "output_path": str(output_path),
        "downloaded_at": str(Path(output_path).stat().st_mtime)
    }

    with open(checksums_file, "w") as f:
        json.dump(checksums_data, f, indent=2)

    logger.info(f"Downloaded {output_path} with checksum {checksum}")
    return {
        "url": url,
        "checksum": checksum,
        "output_path": str(output_path)
    }


def load_huggingface_dataset(dataset_name: str, split: str = "train") -> Any:
    """
    Load a dataset from HuggingFace Hub.

    Args:
        dataset_name: The name of the dataset on HuggingFace (e.g., "username/dataset_name").
        split: The split to load (e.g., "train", "test", "validation").

    Returns:
        The loaded dataset (Dataset or DatasetDict).

    Raises:
        ImportError: If the datasets library is not installed.
        Exception: If the dataset cannot be loaded.
    """
    if not DATASETS_AVAILABLE:
        raise ImportError(
            "The 'datasets' library is required to load HuggingFace datasets. "
            "Install it with: pip install datasets"
        )

    logger.info(f"Loading HuggingFace dataset: {dataset_name} (split: {split})")

    try:
        dataset = load_dataset(dataset_name, split=split)
        logger.info(f"Successfully loaded dataset: {dataset_name}")
        logger.info(f"Dataset shape: {len(dataset)} rows")
        if len(dataset) > 0:
            logger.info(f"Dataset features: {dataset.column_names}")
        return dataset
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_name}: {str(e)}")
        raise


def apply_deferral_flags(df: Any) -> Any:
    """
    Implement deferral flag logic (timeout without action) in the dataset.

    This function inspects the DataFrame columns to identify potential
    'timeout' or 'action' indicators and sets a binary 'deferral' column.

    Logic:
    1. If 'timeout' (or 'is_timeout') exists and is True -> deferral = 1
    2. Else if 'action' (or 'response') exists and is empty/None/NaN -> deferral = 1
    3. Else -> deferral = 0

    Args:
        df: A pandas DataFrame loaded from a dataset.

    Returns:
        The DataFrame with an added 'deferral' column (0 or 1).
    """
    import pandas as pd

    logger.info("Applying deferral flag logic...")
    df = df.copy()

    # Normalize column names for easier matching
    cols_lower = {c.lower(): c for c in df.columns}

    # Identify timeout column
    timeout_col = None
    for candidate in ['timeout', 'is_timeout', 'time_out', 'timed_out']:
        if candidate in cols_lower:
            timeout_col = cols_lower[candidate]
            break

    # Identify action/response column
    action_col = None
    for candidate in ['action', 'response', 'choice', 'selected_option']:
        if candidate in cols_lower:
            action_col = cols_lower[candidate]
            break

    # Initialize deferral column
    df['deferral'] = 0

    # Apply logic
    if timeout_col:
        # If timeout column exists, mark those rows as deferral
        mask_timeout = df[timeout_col].fillna(False)
        df.loc[mask_timeout, 'deferral'] = 1
        logger.info(f"Marked {mask_timeout.sum()} rows as deferral based on '{timeout_col}'")

    if action_col:
        # If action column exists, check for empty/missing values
        # Only mark as deferral if not already marked by timeout (unless we want to override)
        # Assuming timeout takes precedence or they are mutually exclusive in raw data
        # We check for NaN, None, empty string, or explicit "deferral" text
        mask_empty = df[action_col].isna() | (df[action_col].astype(str).str.strip() == '')

        # If timeout wasn't the source, use action column
        if not timeout_col:
            df.loc[mask_empty, 'deferral'] = 1
            logger.info(f"Marked {mask_empty.sum()} rows as deferral based on empty '{action_col}'")
        else:
            # If timeout exists, we might only care about action for non-timeouts
            # Or we might want to flag if action is missing even without timeout flag
            # For this implementation, we assume timeout is the primary indicator.
            # However, if action is missing AND timeout is False/missing, it's likely a deferral.
            mask_deferral_action = mask_empty & ~df[timeout_col].fillna(False)
            df.loc[mask_deferral_action, 'deferral'] = 1
            logger.info(f"Marked additional {mask_deferral_action.sum()} rows as deferral based on missing action.")

    # Summary
    total_deferrals = df['deferral'].sum()
    logger.info(f"Total deferral events identified: {total_deferrals} ({total_deferrals/len(df)*100:.2f}%)")

    return df


def main():
    """
    Main entry point for the ingestion script.
    Loads the PhillyMac dataset, applies deferral flags, and saves to processed data.
    """
    config = get_config()

    # Load the PhillyMac dataset as per T016
    dataset_name = config.get("dataset_phillymac", "PhillyMac/Decision_Making_Content_1")

    if not DATASETS_AVAILABLE:
        logger.error("Cannot proceed without 'datasets' library. Please install it.")
        return

    try:
        dataset = load_huggingface_dataset(dataset_name)

        # Convert to pandas DataFrame
        df = dataset.to_pandas()

        # Apply deferral flag logic (T017)
        df_processed = apply_deferral_flags(df)

        # Save to processed data directory
        output_dir = get_path("data/processed")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "phillymac_decision_making_deferral.csv"

        df_processed.to_csv(output_file, index=False)
        logger.info(f"Saved processed dataset with deferral flags to {output_file}")
        logger.info(f"Dataset saved with {len(df_processed)} rows and columns: {list(df_processed.columns)}")

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        raise


if __name__ == "__main__":
    # Configure basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()