"""
Data loading module for OpenML and UCI datasets.
Handles fetching, validation, and caching.
"""
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
from openml import datasets as openml_datasets
from openml.exceptions import OpenMLServerException

from code.config import PROJECT_ROOT, MIN_SAMPLES, MAX_SAMPLES

logger = logging.getLogger(__name__)

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

def _get_cache_path(dataset_id: int) -> Path:
    return RAW_DATA_DIR / f"dataset_{dataset_id}.json"

def _get_data_path(dataset_id: int) -> Path:
    return RAW_DATA_DIR / f"dataset_{dataset_id}.npz"

def _fetch_from_openml(dataset_id: int) -> Tuple[np.ndarray, np.ndarray, str]:
    """
    Fetch dataset from OpenML.
    Returns X, y, and dataset name.
    """
    try:
        dataset = openml_datasets.get_dataset(dataset_id)
        X, y, _, _ = dataset.get_data(target=dataset.default_target_attribute, dataset_format="array")
        return X, y, dataset.name
    except OpenMLServerException as e:
        logger.error(f"OpenML server error for dataset {dataset_id}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error fetching dataset {dataset_id}: {e}")
        raise

def load_datasets(dataset_ids: List[int]) -> List[Dict[str, Any]]:
    """
    Load multiple datasets, validating sample sizes and caching.

    Args:
        dataset_ids: List of OpenML dataset IDs.

    Returns:
        List of dictionaries with 'id', 'name', 'X', 'y'.
    """
    loaded_datasets = []

    for dataset_id in dataset_ids:
        logger.info(f"Loading dataset {dataset_id}...")
        
        # Check cache
        data_path = _get_data_path(dataset_id)
        if data_path.exists():
            logger.info(f"Loading dataset {dataset_id} from cache.")
            try:
                data = np.load(data_path, allow_pickle=True)
                X = data['X']
                y = data['y']
                name = str(data['name'])
                # Basic validation
                if len(X) < MIN_SAMPLES or len(X) > MAX_SAMPLES:
                    logger.warning(f"Dataset {dataset_id} from cache violates sample size constraints. Skipping.")
                    continue
                loaded_datasets.append({"id": dataset_id, "name": name, "X": X, "y": y})
                continue
            except Exception as e:
                logger.warning(f"Corrupt cache for {dataset_id}: {e}. Re-fetching.")

        # Fetch from OpenML
        try:
            X, y, name = _fetch_from_openml(dataset_id)
            
            # Validation
            n_samples = len(X)
            if n_samples < MIN_SAMPLES:
                logger.warning(f"Dataset {dataset_id} has {n_samples} samples (< {MIN_SAMPLES}). Skipping.")
                continue
            if n_samples > MAX_SAMPLES:
                logger.warning(f"Dataset {dataset_id} has {n_samples} samples (> {MAX_SAMPLES}). Skipping.")
                continue

            # Binary class validation
            unique_classes = np.unique(y)
            if len(unique_classes) != 2:
                logger.warning(f"Dataset {dataset_id} is not binary classification ({len(unique_classes)} classes). Skipping.")
                continue

            # Cache
            np.savez(data_path, X=X, y=y, name=name)
            logger.info(f"Cached dataset {dataset_id}.")

            loaded_datasets.append({"id": dataset_id, "name": name, "X": X, "y": y})

        except Exception as e:
            logger.error(f"Failed to load dataset {dataset_id}: {e}. Skipping.")
            continue

    if len(loaded_datasets) < 15:
        logger.warning(f"Only {len(loaded_datasets)} valid datasets loaded. Expected 15.")
        # Depending on strictness, we might raise, but T005 logic says "log warning and skip"
        # However, T005 also says "If count < 15, raise critical error".
        # We will raise here to be safe.
        raise RuntimeError(f"Insufficient valid datasets loaded: {len(loaded_datasets)} < 15.")

    # Spectrum validation
    sample_sizes = [d["X"].shape[0] for d in loaded_datasets]
    logger.info(f"Sample size range: {min(sample_sizes)} - {max(sample_sizes)}")
    
    return loaded_datasets
