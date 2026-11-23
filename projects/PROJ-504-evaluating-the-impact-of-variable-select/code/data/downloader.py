"""
Data downloader module for fetching regression datasets from OpenML.

This module handles:
- Fetching datasets from OpenML with retry logic and exponential backoff.
- Computing and verifying SHA-256 checksums for data integrity.
- Validating dataset properties (rows, features, condition number).
- Logging warnings for datasets that exceed condition number thresholds.
"""

from __future__ import annotations

import os
import hashlib
import json
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from openml import datasets as openml_datasets
from openml.exceptions import OpenMLServerException

from utils.logger import get_logger, log_exception
from config import get_config

# Condition number threshold for multicollinearity check
CONDITION_NUMBER_THRESHOLD = 1e10


@dataclass
class DatasetMetadata:
    """Container for dataset metadata and validation results."""
    dataset_id: int
    name: str
    n_rows: int
    n_features: int
    condition_number: float
    is_valid: bool
    skip_reason: Optional[str] = None
    checksum: Optional[str] = None


def compute_sha256(file_path: str) -> str:
    """
    Compute SHA-256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def load_or_create_checksum_store(store_path: str = "state/checksums.json") -> Dict[str, str]:
    """
    Load checksum store from disk or create a new one.

    Args:
        store_path: Path to the checksum store file.

    Returns:
        Dictionary mapping file paths to their checksums.
    """
    if os.path.exists(store_path):
        with open(store_path, "r") as f:
            return json.load(f)
    return {}


def save_checksum_store(checksums: Dict[str, str], store_path: str = "state/checksums.json") -> None:
    """
    Save checksum store to disk.

    Args:
        checksums: Dictionary of file paths to checksums.
        store_path: Path to the checksum store file.
    """
    os.makedirs(os.path.dirname(store_path), exist_ok=True)
    with open(store_path, "w") as f:
        json.dump(checksums, f, indent=2)


def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """
    Verify file checksum against expected value.

    Args:
        file_path: Path to the file.
        expected_checksum: Expected SHA-256 hash.

    Returns:
        True if checksum matches, False otherwise.
    """
    actual_checksum = compute_sha256(file_path)
    return actual_checksum == expected_checksum


def calculate_condition_number(X: np.ndarray) -> float:
    """
    Calculate the condition number of a matrix.

    Args:
        X: Feature matrix (n_samples, n_features).

    Returns:
        Condition number (ratio of largest to smallest singular value).
    """
    # Add intercept column if not present
    if X.shape[1] > 0:
        X_with_intercept = np.c_[np.ones(X.shape[0]), X]
    else:
        X_with_intercept = X

    try:
        # Use SVD to compute condition number
        s = np.linalg.svd(X_with_intercept, compute_uv=False)
        condition_num = s[0] / s[-1]
        return float(condition_num)
    except np.linalg.LinAlgError:
        # If SVD fails, return infinity
        return float('inf')


def fetch_datasets(
    dataset_ids: List[int],
    max_retries: int = 3,
    base_delay: float = 2.0,
    logger: Optional[logging.Logger] = None
) -> Tuple[List[DatasetMetadata], List[DatasetMetadata]]:
    """
    Fetch datasets from OpenML with retry logic and validation.

    Args:
        dataset_ids: List of OpenML dataset IDs to fetch.
        max_retries: Maximum number of retry attempts.
        base_delay: Base delay for exponential backoff.
        logger: Logger instance (created if None).

    Returns:
        Tuple of (valid_datasets, skipped_datasets).
    """
    if logger is None:
        logger = get_logger(__name__)

    valid_datasets = []
    skipped_datasets = []

    for dataset_id in dataset_ids:
        dataset_obj = None
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                logger.info(f"Fetching dataset ID {dataset_id} (attempt {retry_count + 1}/{max_retries})")
                dataset_obj = openml_datasets.get_dataset(dataset_id)
                break
            except OpenMLServerException as e:
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error(f"Failed to fetch dataset {dataset_id} after {max_retries} retries: {e}")
                    break
                
                delay = base_delay * (2 ** (retry_count - 1))
                logger.warning(f"Retry {retry_count}/{max_retries} for dataset {dataset_id} in {delay:.1f}s")
                time.sleep(delay)
            except Exception as e:
                logger.error(f"Unexpected error fetching dataset {dataset_id}: {e}")
                log_exception(logger, f"Error fetching dataset {dataset_id}")
                break

        if dataset_obj is None:
            continue

        try:
            # Download and get data
            X, y, categorical, attribute_names = dataset_obj.get_data(
                dataset_format="array",
                target=dataset_obj.default_target_attribute
            )

            # Convert to numpy arrays if needed
            if not isinstance(X, np.ndarray):
                X = np.array(X)
            if not isinstance(y, np.ndarray):
                y = np.array(y)

            n_rows = X.shape[0]
            n_features = X.shape[1]

            # Validate minimum requirements
            if n_rows < 100:
                skip_reason = f"Insufficient rows: {n_rows} < 100"
                skipped_datasets.append(DatasetMetadata(
                    dataset_id=dataset_id,
                    name=dataset_obj.name,
                    n_rows=n_rows,
                    n_features=n_features,
                    condition_number=0.0,
                    is_valid=False,
                    skip_reason=skip_reason
                ))
                logger.warning(f"Skipping dataset {dataset_id} ({dataset_obj.name}): {skip_reason}")
                continue

            if n_features < 3:
                skip_reason = f"Insufficient features: {n_features} < 3"
                skipped_datasets.append(DatasetMetadata(
                    dataset_id=dataset_id,
                    name=dataset_obj.name,
                    n_rows=n_rows,
                    n_features=n_features,
                    condition_number=0.0,
                    is_valid=False,
                    skip_reason=skip_reason
                ))
                logger.warning(f"Skipping dataset {dataset_id} ({dataset_obj.name}): {skip_reason}")
                continue

            # Calculate condition number
            condition_number = calculate_condition_number(X)
            
            # Check condition number threshold
            if condition_number > CONDITION_NUMBER_THRESHOLD:
                skip_reason = f"Condition number too high: {condition_number:.2e} > {CONDITION_NUMBER_THRESHOLD:.2e}"
                skipped_datasets.append(DatasetMetadata(
                    dataset_id=dataset_id,
                    name=dataset_obj.name,
                    n_rows=n_rows,
                    n_features=n_features,
                    condition_number=condition_number,
                    is_valid=False,
                    skip_reason=skip_reason
                ))
                logger.warning(f"Skipping dataset {dataset_id} ({dataset_obj.name}): {skip_reason}")
                continue

            # Compute checksum
            checksum = compute_sha256(dataset_obj.data_file)

            valid_datasets.append(DatasetMetadata(
                dataset_id=dataset_id,
                name=dataset_obj.name,
                n_rows=n_rows,
                n_features=n_features,
                condition_number=condition_number,
                is_valid=True,
                checksum=checksum
            ))
            
            logger.info(f"Successfully validated dataset {dataset_id} ({dataset_obj.name}): "
                        f"{n_rows} rows, {n_features} features, cond={condition_number:.2e}")

        except Exception as e:
            logger.error(f"Error processing dataset {dataset_id}: {e}")
            log_exception(logger, f"Error processing dataset {dataset_id}")
            skipped_datasets.append(DatasetMetadata(
                dataset_id=dataset_id,
                name=dataset_obj.name,
                n_rows=0,
                n_features=0,
                condition_number=0.0,
                is_valid=False,
                skip_reason=f"Processing error: {str(e)}"
            ))

    return valid_datasets, skipped_datasets


def main():
    """
    Main entry point for the downloader module.
    
    Fetches datasets from OpenML, validates them, and logs results.
    """
    logger = get_logger(__name__)
    logger.info("Starting dataset download and validation")

    config = get_config()
    dataset_ids = config.openml_ids

    logger.info(f"Fetching {len(dataset_ids)} datasets from OpenML: {dataset_ids}")

    valid_datasets, skipped_datasets = fetch_datasets(
        dataset_ids=dataset_ids,
        logger=logger
    )

    logger.info(f"Validation complete: {len(valid_datasets)} valid, {len(skipped_datasets)} skipped")

    if len(valid_datasets) == 0:
        logger.error("No valid datasets found. Aborting.")
        raise RuntimeError("No valid datasets found after validation")

    # Log skipped datasets details
    for skipped in skipped_datasets:
        logger.warning(f"Skipped dataset {skipped.dataset_id} ({skipped.name}): {skipped.skip_reason}")

    # Save validation results
    results = {
        "valid": [
            {
                "dataset_id": d.dataset_id,
                "name": d.name,
                "n_rows": d.n_rows,
                "n_features": d.n_features,
                "condition_number": d.condition_number,
                "checksum": d.checksum
            }
            for d in valid_datasets
        ],
        "skipped": [
            {
                "dataset_id": d.dataset_id,
                "name": d.name,
                "reason": d.skip_reason
            }
            for d in skipped_datasets
        ]
    }

    output_path = os.path.join(config.output_path, "data", "raw")
    os.makedirs(output_path, exist_ok=True)
    
    results_file = os.path.join(output_path, "validation_results.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Validation results saved to {results_file}")

    return valid_datasets, skipped_datasets


if __name__ == "__main__":
    main()