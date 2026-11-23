"""
Data loading module with strict "fail loud" logic.

This module provides functions to load real regression datasets from verified
sources (OpenML via scikit-learn). It explicitly forbids synthetic data generation
or fallbacks. If a real data source cannot be accessed, the loader raises an error.
"""
import logging
from typing import Tuple, Dict, Any
from sklearn.datasets import fetch_openml
import pandas as pd
import numpy as np

from utils.logging import get_logger

logger = get_logger(__name__)

# Verified real data sources (OpenML dataset IDs)
# These are public regression benchmarks available via OpenML
DATA_SOURCES = {
    "boston": {
        "id": 531,
        "name": "boston",
        "description": "Boston Housing Prices",
        "target": "MEDV",
        "is_regression": True
    },
    "california": {
        "id": 1320,
        "name": "california",
        "description": "California Housing Prices",
        "target": "MedHouseVal",
        "is_regression": True
    },
    "airline": {
        "id": 42181,
        "name": "airline",
        "description": "Airline Passenger Forecasting",
        "target": "Y",
        "is_regression": True
    },
    "wine_quality_red": {
        "id": 1897,
        "name": "wine_quality_red",
        "description": "Wine Quality (Red)",
        "target": "quality",
        "is_regression": True
    },
    "bike": {
        "id": 42078,
        "name": "bike",
        "description": "Bike Sharing Demand",
        "target": "count",
        "is_regression": True
    }
}

def load_regression_dataset(
    source_key: str,
    cache: bool = True,
    shuffle: bool = False
) -> Tuple[pd.DataFrame, pd.Series, Dict[str, Any]]:
    """
    Load a real regression dataset from a verified OpenML source.
    
    This function strictly adheres to "fail loud" principles:
    - No synthetic data generation
    - No fallback to mock data
    - Raises explicit errors if the real source is unreachable
    
    Args:
        source_key: Key from DATA_SOURCES dictionary (e.g., "boston", "california")
        cache: Whether to use local cache (default: True)
        shuffle: Whether to shuffle the dataset (default: False)
        
    Returns:
      Tuple of (features_df, target_series, metadata_dict)
      
    Raises:
        ValueError: If source_key is not found in DATA_SOURCES
        RuntimeError: If the dataset cannot be fetched from OpenML
        Exception: Any other error during data fetching
    """
    if source_key not in DATA_SOURCES:
        raise ValueError(
            f"Unknown data source: '{source_key}'. "
            f"Available sources: {list(DATA_SOURCES.keys())}"
        )
    
    source_info = DATA_SOURCES[source_key]
    dataset_id = source_info["id"]
    target_name = source_info["target"]
    
    logger.info(
        f"Loading dataset '{source_key}' (OpenML ID: {dataset_id}) "
        f"target: '{target_name}'"
    )
    
    try:
        # Fetch from OpenML - this is the ONLY data source
        # No try/except block that falls back to synthetic data
        dataset = fetch_openml(
            data_id=dataset_id,
            as_frame=True,
            cache=cache,
            shuffle=shuffle
        )
        
        # Validate that we got a DataFrame
        if not isinstance(dataset.data, pd.DataFrame):
            raise RuntimeError(
                f"Expected DataFrame from OpenML for '{source_key}', "
                f"got {type(dataset.data)}"
            )
        
        # Validate target exists
        if target_name not in dataset.target_names:
            raise RuntimeError(
                f"Target '{target_name}' not found in dataset '{source_key}'. "
                f"Available targets: {dataset.target_names}"
            )
        
        # Extract features and target
        features = dataset.data
        target = dataset.target[target_name]
        
        # Ensure target is numeric (some datasets might have string targets)
        if not np.issubdtype(target.dtype, np.number):
            # Try to convert, but fail if it doesn't work
            try:
                target = pd.to_numeric(target, errors='raise')
            except (ValueError, TypeError) as e:
                raise RuntimeError(
                    f"Cannot convert target '{target_name}' to numeric for "
                    f"dataset '{source_key}'. Original dtype: {target.dtype}"
                ) from e
        
        metadata = {
            "source_key": source_key,
            "dataset_id": dataset_id,
            "name": source_info["name"],
            "description": source_info["description"],
            "target": target_name,
            "n_samples": len(target),
            "n_features": len(features.columns),
            "feature_names": list(features.columns),
            "target_dtype": str(target.dtype),
            "is_regression": source_info["is_regression"]
        }
        
        logger.info(
            f"Successfully loaded '{source_key}': "
            f"{metadata['n_samples']} samples, {metadata['n_features']} features"
        )
        
        return features, target, metadata
        
    except Exception as e:
        # Fail loudly - do not catch and fallback
        logger.error(
            f"Failed to load dataset '{source_key}' from OpenML (ID: {dataset_id}). "
            f"This is a real data source error - no synthetic fallback available."
        )
        raise RuntimeError(
            f"Failed to fetch real dataset '{source_key}' from OpenML. "
            f"Check your internet connection and OpenML availability. "
            f"Original error: {str(e)}"
        ) from e