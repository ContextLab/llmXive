"""
Data downloader module for fetching regression datasets from OpenML.

This module handles:
- Fetching datasets from OpenML with retry logic.
- Validating dataset properties (rows, predictors).
- Filtering datasets based on multicollinearity (condition number).
- Saving raw data to disk.
"""

import os
import hashlib
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

import numpy as np
import openml
from sklearn.feature_selection import VarianceThreshold
from scipy.linalg import cond

# Import project utilities using the defined API surface
from utils.logger import get_logger, log_exception
from config import get_config

# Constants for condition number threshold
CONDITION_NUMBER_THRESHOLD = 1e10

@dataclass
class DatasetMetadata:
    """Container for dataset metadata and properties."""
    dataset_id: int
    name: str
    n_rows: int
    n_predictors: int
    condition_number: float
    target_column: str
    path: str
    checksum: str
    is_valid: bool
    skip_reason: Optional[str] = None

def _calculate_checksum(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def _get_condition_number(X: np.ndarray) -> float:
    """
    Calculate the condition number of the feature matrix.
    Uses the 2-norm (default for scipy.linalg.cond).
    """
    if X.shape[1] == 0:
        return np.inf
    # Add a small epsilon to avoid division by zero if matrix is singular
    # but scipy.linalg.cond handles singular matrices by returning inf.
    return cond(X, 2)

def fetch_datasets(
    dataset_ids: Optional[List[int]] = None,
    n_datasets: int = 10,
    min_rows: int = 100,
    min_predictors: int = 3,
    logger_name: str = "data.downloader"
) -> List[DatasetMetadata]:
    """
    Fetch regression datasets from OpenML.

    Args:
        dataset_ids: Optional list of specific OpenML IDs to fetch.
        n_datasets: Number of datasets to fetch if IDs not provided.
        min_rows: Minimum number of rows required.
        min_predictors: Minimum number of predictors required.
        logger_name: Name for the logger instance.

    Returns:
        List of DatasetMetadata objects for valid datasets.
    """
    logger = get_logger(logger_name)
    logger.info(f"Starting dataset fetch. Target: {n_datasets} datasets.")
    
    config = get_config()
    output_path = config.output_path if hasattr(config, 'output_path') else "data/processed"
    raw_path = os.path.join(output_path, "..", "raw")
    os.makedirs(raw_path, exist_ok=True)

    datasets_to_process = []
    
    if dataset_ids:
        datasets_to_process = dataset_ids
    else:
        # Fetch a list of available regression datasets
        try:
            # Search for regression tasks
            tasks = openml.tasks.list_tasks(task_type_id=1, size=n_datasets * 2) # Fetch extra to filter
            # Extract dataset IDs from tasks
            dataset_ids_found = list(set([t.dataset_id for t in tasks.values()]))
            # Shuffle to get diverse set
            np.random.shuffle(dataset_ids_found)
            datasets_to_process = dataset_ids_found[:n_datasets * 2] # Try more than needed
        except Exception as e:
            logger.error(f"Failed to list OpenML tasks: {e}")
            raise

    valid_datasets = []
    attempts = 0
    max_retries = 3

    for did in datasets_to_process:
        if len(valid_datasets) >= n_datasets:
            break
        
        attempts += 1
        logger.info(f"Processing OpenML ID: {did} (Attempt {attempts})")
        
        dataset_metadata = None
        
        for retry in range(max_retries):
            try:
                # Fetch dataset
                dataset = openml.datasets.get_dataset(did)
                
                # Convert to pandas dataframe
                X, y, categorical, attribute_names = dataset.get_data(
                    dataset_format="dataframe", 
                    target=dataset.default_target_attribute
                )
                
                # Handle target column
                target_col = dataset.default_target_attribute
                if target_col not in X.columns:
                    # Sometimes target is separated, ensure we have X and y separate
                    # openml.get_data returns X (features) and y (target) if target specified
                    pass 
                
                # Ensure X is numeric
                X_numeric = X.select_dtypes(include=[np.number])
                
                n_rows = X_numeric.shape[0]
                n_predictors = X_numeric.shape[1]
                
                # Validation 1: Row count
                if n_rows < min_rows:
                    logger.warning(f"Dataset {did} has {n_rows} rows (< {min_rows}). Skipping.")
                    dataset_metadata = DatasetMetadata(
                        dataset_id=did,
                        name=dataset.name,
                        n_rows=n_rows,
                        n_predictors=n_predictors,
                        condition_number=0.0,
                        target_column=target_col,
                        path="",
                        checksum="",
                        is_valid=False,
                        skip_reason=f"Rows < {min_rows}"
                    )
                    break
                
                # Validation 2: Predictor count
                if n_predictors < min_predictors:
                    logger.warning(f"Dataset {did} has {n_predictors} predictors (< {min_predictors}). Skipping.")
                    dataset_metadata = DatasetMetadata(
                        dataset_id=did,
                        name=dataset.name,
                        n_rows=n_rows,
                        n_predictors=n_predictors,
                        condition_number=0.0,
                        target_column=target_col,
                        path="",
                        checksum="",
                        is_valid=False,
                        skip_reason=f"Predictors < {min_predictors}"
                    )
                    break

                # Validation 3: Condition Number (Multicollinearity Check)
                # Convert to numpy array for condition number calculation
                X_array = X_numeric.values
                cond_num = _get_condition_number(X_array)
                
                # T014 Implementation: Skip datasets with condition number > 10^10
                if cond_num > CONDITION_NUMBER_THRESHOLD:
                    warning_msg = (
                        f"Dataset {did} ({dataset.name}) has condition number {cond_num:.2e} "
                        f"(> {CONDITION_NUMBER_THRESHOLD:.2e}). Skipping due to extreme multicollinearity."
                    )
                    logger.warning(warning_msg)
                    
                    dataset_metadata = DatasetMetadata(
                        dataset_id=did,
                        name=dataset.name,
                        n_rows=n_rows,
                        n_predictors=n_predictors,
                        condition_number=cond_num,
                        target_column=target_col,
                        path="",
                        checksum="",
                        is_valid=False,
                        skip_reason=f"Condition number {cond_num:.2e} > {CONDITION_NUMBER_THRESHOLD:.2e}"
                    )
                    break
                
                # If passed all checks
                # Save raw data
                safe_name = dataset.name.replace(" ", "_").replace("/", "_")
                file_path = os.path.join(raw_path, f"{safe_name}_{did}.csv")
                X_numeric.to_csv(file_path, index=False)
                
                # Calculate checksum
                checksum = _calculate_checksum(file_path)
                
                dataset_metadata = DatasetMetadata(
                    dataset_id=did,
                    name=dataset.name,
                    n_rows=n_rows,
                    n_predictors=n_predictors,
                    condition_number=cond_num,
                    target_column=target_col,
                    path=file_path,
                    checksum=checksum,
                    is_valid=True
                )
                valid_datasets.append(dataset_metadata)
                logger.info(f"Successfully saved dataset {did}: {dataset.name}")
                break # Success, break retry loop
                
            except Exception as e:
                logger.warning(f"Error fetching dataset {did} (retry {retry+1}/{max_retries}): {e}")
                if retry == max_retries - 1:
                    logger.error(f"Failed to fetch dataset {did} after {max_retries} retries.")
                    dataset_metadata = DatasetMetadata(
                        dataset_id=did,
                        name=f"Unknown_{did}",
                        n_rows=0,
                        n_predictors=0,
                        condition_number=0.0,
                        target_column="",
                        path="",
                        checksum="",
                        is_valid=False,
                        skip_reason=f"Fetch failed: {str(e)}"
                    )
                else:
                    time.sleep(2 ** retry) # Exponential backoff

    logger.info(f"Completed. Valid datasets: {len(valid_datasets)}/{n_datasets}")
    return valid_datasets

def main():
    """Entry point for the downloader script."""
    logger = get_logger("data.downloader.main")
    logger.info("Running downloader main.")
    
    try:
        # Fetch 10 datasets as per requirements
        datasets = fetch_datasets(n_datasets=10)
        
        valid_count = sum(1 for d in datasets if d.is_valid)
        skipped_count = len(datasets) - valid_count
        
        logger.info(f"Summary: {valid_count} valid, {skipped_count} skipped.")
        
        # Log details of skipped datasets for debugging
        for d in datasets:
            if not d.is_valid:
                logger.info(f"Skipped: ID={d.dataset_id}, Name={d.name}, Reason={d.skip_reason}")
                
        return datasets
        
    except Exception as e:
        log_exception(logger, "Fatal error in downloader main", exc_info=True)
        raise

if __name__ == "__main__":
    main()
