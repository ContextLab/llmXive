"""
Configuration module for the Avian Foraging Behavior Prediction Pipeline.

This module defines all paths, random seeds, and constants required for
reproducibility and consistent execution across the pipeline.
"""

import os
import random
from pathlib import Path
from typing import Dict, Any, Optional, List
import numpy as np
import sys

# --- Constants ---

# Random seed for reproducibility across all random operations
RANDOM_SEED: int = 42

# URLs for external data sources
# EBD: eBird Basic Dataset (S3 path)
EBD_URL: str = "s3://ebird-data/ebd_release/"

# NLCD: National Land Cover Database 2021 (HuggingFace dataset path)
# Using the verified source as per T060 requirements
NLCD_URL: str = "usgs/nlcd_2021/landcover"

# Buffer size in meters for land cover analysis
BUFFER_SIZE: int = 100

# Number of permutations for statistical testing
N_PERMUTATIONS: int = 1000

# --- Project Root Detection ---

def get_project_root() -> Path:
    """
    Returns the project root directory.
    Assumes the script is run from within the 'code' directory or its subdirectories.
    """
    current_file = Path(__file__).resolve()
    # The project root is two levels up from utils/config.py
    # Structure: code/utils/config.py -> code/ -> project_root/
    return current_file.parent.parent.parent

def get_code_root() -> Path:
    """Returns the code directory root."""
    return get_project_root() / "code"

def get_data_dir() -> Path:
    """Returns the data directory root."""
    return get_code_root() / "data"

def get_raw_data_dir() -> Path:
    """Returns the raw data directory."""
    return get_data_dir() / "raw"

def get_processed_dir() -> Path:
    """Returns the processed data directory."""
    return get_data_dir() / "processed"

def get_models_dir() -> Path:
    """Returns the models directory."""
    return get_code_root() / "models"

def get_viz_dir() -> Path:
    """Returns the visualization directory."""
    return get_code_root() / "viz"

def get_figures_dir() -> Path:
    """Returns the figures directory (often inside viz or data)."""
    return get_viz_dir() / "figures"

def get_reports_dir() -> Path:
    """Returns the reports directory."""
    return get_viz_dir() / "reports"

def get_metadata_file() -> Path:
    """Returns the path to the metadata.yaml file."""
    return get_data_dir() / "metadata.yaml"

# --- Path Helpers ---

def get_file_path(relative_path: str) -> Path:
    """
    Constructs an absolute path relative to the project root.

    Args:
        relative_path: Path relative to project root.

    Returns:
        Absolute Path object.
    """
    return get_project_root() / relative_path

def get_file_paths(*relative_paths: str) -> List[Path]:
    """
    Constructs multiple absolute paths.

    Returns:
        List of Path objects.
    """
    return [get_file_path(p) for p in relative_paths]

def ensure_directories() -> None:
    """
    Creates all necessary directories if they do not exist.
    """
    dirs = [
        get_raw_data_dir(),
        get_processed_dir(),
        get_models_dir(),
        get_figures_dir(),
        get_reports_dir(),
        get_data_dir(),
        get_code_root(),
        get_viz_dir(),
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# --- Logging ---

def get_logger(name: str = "pipeline") -> Any:
    """
    Configures and returns a logger for the pipeline.

    Args:
        name: Logger name.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

# --- Reproducibility ---

def set_seed(seed: Optional[int] = None) -> None:
    """
    Sets the random seed for Python, NumPy, and random modules.

    Args:
        seed: The seed value. Defaults to RANDOM_SEED.
    """
    if seed is None:
        seed = RANDOM_SEED
    
    random.seed(seed)
    np.random.seed(seed)
    
    # If torch is available, set seed there too (future proofing)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

def get_seed() -> int:
    """Returns the current random seed."""
    return RANDOM_SEED

# --- Model Parameters ---

def get_model_params() -> Dict[str, Any]:
    """
    Returns default parameters for the classification model.

    Returns:
        Dictionary of model hyperparameters.
    """
    return {
        'random_state': RANDOM_SEED,
        'max_iter': 1000,
        'solver': 'lbfgs',
        'multi_class': 'multinomial',
        'C': 1.0,
        'penalty': 'l2'
    }

def get_cv_params() -> Dict[str, Any]:
    """
    Returns parameters for cross-validation.

    Returns:
        Dictionary of CV parameters.
    """
    return {
        'n_splits': 5,
        'shuffle': True,
        'random_state': RANDOM_SEED
    }

def get_permutation_params() -> Dict[str, Any]:
    """
    Returns parameters for permutation testing.

    Returns:
        Dictionary of permutation parameters.
    """
    return {
        'n_permutations': N_PERMUTATIONS,
        'random_state': RANDOM_SEED
    }

def get_data_thresholds() -> Dict[str, Any]:
    """
    Returns data quality thresholds.

    Returns:
        Dictionary of thresholds.
    """
    return {
        'min_observations_per_species': 50,
        'buffer_size_meters': BUFFER_SIZE,
        'max_null_ratio': 0.05
    }

# Import logging here to avoid circular imports if placed at top
import logging