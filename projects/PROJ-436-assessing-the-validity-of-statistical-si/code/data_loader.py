"""
Data loading module for RCT datasets from OpenML.

This module handles downloading, caching, and validating RCT datasets.
It strictly enforces failure-on-missing behavior: if a dataset ID is not
found or the download fails, it raises a DataLoadError. No synthetic
data fallbacks are implemented.
"""

import os
import sys
import logging
from typing import Optional, Union, List, Dict, Any
from pathlib import Path

import openml
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DataLoadError(Exception):
    """Custom exception for data loading failures."""
    pass

def get_openml_dataset(dataset_id: int) -> openml.datasets.OpenMLDataset:
    """
    Download or retrieve a dataset from OpenML by ID.

    Args:
        dataset_id: The OpenML dataset ID.

    Returns:
        The OpenML dataset object.

    Raises:
        DataLoadError: If the dataset cannot be found or downloaded.
    """
    try:
        logger.info(f"Fetching dataset {dataset_id} from OpenML...")
        dataset = openml.datasets.get_dataset(dataset_id)
        logger.info(f"Successfully retrieved dataset: {dataset.name} (ID: {dataset_id})")
        return dataset
    except openml.exceptions.OpenMLServerException as e:
        if "not found" in str(e).lower():
            raise DataLoadError(f"Dataset with ID {dataset_id} not found on OpenML.") from e
        raise DataLoadError(f"OpenML server error while fetching dataset {dataset_id}: {e}") from e
    except Exception as e:
        raise DataLoadError(f"Failed to download dataset {dataset_id}: {e}") from e

def load_dataset_as_dataframe(
    dataset: openml.datasets.OpenMLDataset,
    target: Optional[str] = None,
    exclude_features: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Convert an OpenML dataset to a pandas DataFrame.

    Args:
        dataset: The OpenML dataset object.
        target: The name of the target column (optional).
        exclude_features: List of feature names to exclude (optional).

    Returns:
        A pandas DataFrame containing the dataset.

    Raises:
        DataLoadError: If the dataset cannot be converted to a DataFrame.
    """
    try:
        # Get the data as a DataFrame
        X, y, categorical_indicator, feature_names = dataset.get_data(
            target=target,
            dataset_format="dataframe"
        )
        
        # If target is provided and exists, ensure it's in the dataframe
        if target and y is not None:
            if target not in X.columns:
                X[target] = y

        # Exclude features if specified
        if exclude_features:
            X = X.drop(columns=[f for f in exclude_features if f in X.columns])

        logger.info(f"Loaded dataset with shape: {X.shape}")
        return X
    except Exception as e:
        raise DataLoadError(f"Failed to convert dataset to DataFrame: {e}") from e

def validate_rct_dataset(df: pd.DataFrame, min_rows: int = 100) -> bool:
    """
    Validate that a dataset meets minimum requirements for RCT analysis.

    Args:
        df: The pandas DataFrame to validate.
        min_rows: Minimum number of rows required (default: 100).

    Returns:
        True if the dataset is valid, False otherwise.

    Raises:
        DataLoadError: If the dataset has fewer rows than the minimum threshold.
    """
    if len(df) < min_rows:
        logger.warning(f"Dataset has {len(df)} rows, which is less than the minimum {min_rows}. Skipping.")
        raise DataLoadError(f"Dataset has {len(df)} rows, which is less than the minimum required {min_rows} rows.")
    
    # Check for essential columns (treatment, outcome)
    # We assume these will be identified later, but we check for basic structure
    if df.empty:
        raise DataLoadError("Dataset is empty.")
    
    logger.info(f"Dataset validation passed: {len(df)} rows, {len(df.columns)} columns")
    return True

def load_and_validate(
    dataset_id: int,
    target: Optional[str] = None,
    exclude_features: Optional[List[str]] = None,
    min_rows: int = 100
) -> pd.DataFrame:
    """
    Load and validate a dataset from OpenML.

    This is the main entry point for loading datasets. It performs the
    following steps:
    1. Fetches the dataset from OpenML.
    2. Converts it to a pandas DataFrame.
    3. Validates that it meets minimum requirements.

    Args:
        dataset_id: The OpenML dataset ID.
        target: The name of the target column (optional).
        exclude_features: List of feature names to exclude (optional).
        min_rows: Minimum number of rows required (default: 100).

    Returns:
        A validated pandas DataFrame.

    Raises:
        DataLoadError: If any step fails or validation criteria are not met.
    """
    # Step 1: Get dataset
    dataset = get_openml_dataset(dataset_id)
    
    # Step 2: Convert to DataFrame
    df = load_dataset_as_dataframe(dataset, target, exclude_features)
    
    # Step 3: Validate
    validate_rct_dataset(df, min_rows)
    
    return df

def main():
    """
    Main function to demonstrate dataset loading.
    
    This function attempts to load a known RCT dataset from OpenML.
    It will fail loudly if the dataset is not available.
    """
    # Example: Load a known RCT dataset (e.g., OpenML ID 42594 - "Pima Indians Diabetes")
    # Note: This is just an example; in production, dataset IDs would be configurable
    example_dataset_id = 42594 
    
    try:
        df = load_and_validate(example_dataset_id)
        logger.info(f"Successfully loaded and validated dataset: {df.shape}")
        logger.info(f"Columns: {list(df.columns)}")
        logger.info(f"First few rows:\n{df.head()}")
    except DataLoadError as e:
        logger.error(f"Data loading failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()