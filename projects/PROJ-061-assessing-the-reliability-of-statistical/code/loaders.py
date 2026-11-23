"""
Dataset loading module for the llmXive statistical power reliability pipeline.

This module handles fetching datasets from UCI/OpenML using the configuration
defined in T004a (code/config.py). It includes checksum validation and PII scanning.
"""
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from datasets import load_dataset
import logging

from config import get_dataset_config

# Configure logging
logger = logging.getLogger(__name__)

# PII patterns to scan for (basic regex patterns for potential sensitive data)
PII_PATTERNS = [
    r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
    r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',  # IP addresses
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
    r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone numbers
]

def compute_checksum(data: Any) -> str:
    """
    Compute a SHA-256 checksum of the provided data.

    Args:
        data: The data to compute the checksum for (can be a dict, list, or string).

    Returns:
        str: The hexadecimal checksum string.
    """
    # Serialize data to JSON string for consistent hashing
    if isinstance(data, (dict, list)):
        json_str = json.dumps(data, sort_keys=True)
    else:
        json_str = str(data)

    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()

def scan_for_pii(data: pd.DataFrame, threshold: int = 10) -> List[str]:
    """
    Scan a DataFrame for potential PII patterns.

    Args:
        data: The DataFrame to scan.
        threshold: Minimum number of matches to flag a column as containing PII.

    Returns:
        List[str]: List of column names that contain potential PII.
    """
    flagged_columns = []

    for col in data.columns:
        # Convert column to string for regex matching
        col_str = data[col].astype(str).str.cat(sep=' ')

        for pattern in PII_PATTERNS:
            matches = re.findall(pattern, col_str)
            if len(matches) >= threshold:
                flagged_columns.append(col)
                logger.warning(f"Potential PII detected in column '{col}' with pattern '{pattern}'")
                break  # No need to check other patterns for this column

    return flagged_columns

def load_dataset(dataset_id: str) -> Tuple[pd.DataFrame, str]:
    """
    Load a dataset from Hugging Face datasets (UCI/OpenML).

    This function fetches the dataset, validates it, and returns the data as a DataFrame.

    Args:
        dataset_id: The ID of the dataset to load (e.g., 'iris', 'wine').

    Returns:
        Tuple[pd.DataFrame, str]: A tuple containing the loaded DataFrame and a checksum.

    Raises:
        ValueError: If the dataset cannot be loaded or contains PII.
        RuntimeError: If the dataset fetch fails.
    """
    logger.info(f"Loading dataset: {dataset_id}")

    try:
        # Load dataset from Hugging Face
        # Using streaming=False to ensure we get the full dataset for validation
        dataset = load_dataset(dataset_id, split="train")

        # Convert to DataFrame
        df = dataset.to_pandas()

        # Verify we have data
        if df.empty:
            raise ValueError(f"Dataset '{dataset_id}' is empty after loading.")

        # Compute checksum of the data
        checksum = compute_checksum(df.to_dict(orient='records'))

        # Scan for PII
        pii_columns = scan_for_pii(df)
        if pii_columns:
            raise ValueError(
                f"Dataset '{dataset_id}' contains potential PII in columns: {pii_columns}. "
                "This dataset cannot be used due to privacy concerns."
            )

        logger.info(f"Successfully loaded '{dataset_id}' with {len(df)} rows. Checksum: {checksum[:16]}...")
        return df, checksum

    except Exception as e:
        # Fail loudly - do not fall back to synthetic data
        error_msg = f"Failed to load dataset '{dataset_id}': {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

def load_all_datasets() -> Dict[str, Dict[str, Any]]:
    """
    Load all datasets defined in the configuration.

    Returns:
        Dict[str, Dict[str, Any]]: A dictionary mapping dataset IDs to their data and metadata.
    """
    datasets_config = get_dataset_config()
    loaded_datasets = {}

    for dataset_info in datasets_config:
        dataset_id = dataset_info['id']
        try:
            df, checksum = load_dataset(dataset_id)
            loaded_datasets[dataset_id] = {
                'data': df,
                'checksum': checksum,
                'outcome_type': dataset_info['outcome_type'],
                'url': dataset_info.get('url', 'N/A')
            }
            logger.info(f"Loaded dataset '{dataset_id}' successfully.")
        except Exception as e:
            logger.error(f"Failed to load dataset '{dataset_id}': {e}")
            # Continue with other datasets, but log the failure

    return loaded_datasets

def get_dataset_info(dataset_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve metadata for a specific dataset from the configuration.

    Args:
        dataset_id: The ID of the dataset to get info for.

    Returns:
        Optional[Dict[str, Any]]: Dictionary containing dataset metadata, or None if not found.
    """
    datasets_config = get_dataset_config()

    for dataset_info in datasets_config:
        if dataset_info['id'] == dataset_id:
            return dataset_info

    logger.warning(f"Dataset '{dataset_id}' not found in configuration.")
    return None
