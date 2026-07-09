"""
Configuration management for dataset URLs and random seeds.

This module provides centralized configuration for:
- Dataset URLs (HuggingFace datasets referenced in research definitions)
- Random seeds for reproducibility
- Processing paths and environment settings
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional

# Project root path
PROJECT_ROOT = Path(__file__).parent.parent

# Dataset configuration
DATASETS: Dict[str, str] = {
    # Primary dataset for decision making (referencing T008.2 trace)
    "textual_decisionmaking": "zhehuderek/textual_decisionmaking_data",
    # Secondary dataset for robustness checks (referencing T008.2 trace)
    "decision_making_content": "PhillyMac/Decision_Making_Content_1",
}

# Random seed configuration
RANDOM_SEED: int = 42

# Processing configuration
CONFIG: Dict[str, Any] = {
    "random_seed": RANDOM_SEED,
    "max_workers": os.cpu_count() or 4,
    "timeout_seconds": 3600,  # 1 hour timeout for data operations
    "chunk_size": 1000,  # Rows to process at a time
}

# Output paths relative to project root
PATHS: Dict[str, Path] = {
    "data_raw": PROJECT_ROOT / "data" / "raw",
    "data_processed": PROJECT_ROOT / "data" / "processed",
    "data_results": PROJECT_ROOT / "data" / "results",
    "code": PROJECT_ROOT / "code",
    "tests": PROJECT_ROOT / "tests",
    "figures": PROJECT_ROOT / "figures",
}

# Model configuration
MODEL_CONFIG: Dict[str, Any] = {
    "random_effect": "participant",
    "fixed_effects": ["regret_proxy", "option_count"],
    "interaction_terms": ["regret_proxy:option_count"],
    "covariates": ["potential_loss_magnitude", "perceived_risk"],
    "vif_threshold": 5.0,
    "cv_folds": 5,
}

# Sensitivity analysis configurations
SENSITIVITY_VARIATIONS: list = [
    "min_max_regret",  # Primary: Opportunity cost
    "utility_variance",  # Spec: SD of Normalized EU
    "price_variance",  # Plan: Price variance proxy
    "attribute_entropy",  # Plan: Attribute entropy
    "attribute_range",  # Spec: Attribute range
    "price_variance_cross",  # Spec: Duplicate for cross-check
]

def get_dataset_url(dataset_name: str) -> str:
    """
    Retrieve the URL/name for a registered dataset.

    Args:
        dataset_name: Key from DATASETS dict (e.g., 'textual_decisionmaking')

    Returns:
        The dataset identifier string

    Raises:
        KeyError: If dataset_name is not registered
    """
    if dataset_name not in DATASETS:
        raise KeyError(f"Dataset '{dataset_name}' not found in configuration. "
                     f"Available: {list(DATASETS.keys())}")
    return DATASETS[dataset_name]

def get_path(path_name: str) -> Path:
    """
    Retrieve a configured path.

    Args:
        path_name: Key from PATHS dict (e.g., 'data_raw')

    Returns:
        The resolved Path object

    Raises:
        KeyError: If path_name is not registered
    """
    if path_name not in PATHS:
        raise KeyError(f"Path '{path_name}' not found in configuration. "
                     f"Available: {list(PATHS.keys())}")
    return PATHS[path_name]

def ensure_paths_exist() -> None:
    """Create all configured directories if they don't exist."""
    for path in PATHS.values():
        path.mkdir(parents=True, exist_ok=True)

def get_config(key: str) -> Any:
    """
    Retrieve a configuration value by key.

    Args:
        key: Configuration key (e.g., 'random_seed', 'max_workers')

    Returns:
        The configuration value
    """
    if key not in CONFIG:
        raise KeyError(f"Config key '{key}' not found. Available: {list(CONFIG.keys())}")
    return CONFIG[key]

def get_model_config(key: str) -> Any:
    """
    Retrieve a model configuration value by key.

    Args:
        key: Model config key (e.g., 'vif_threshold', 'cv_folds')

    Returns:
        The model configuration value
    """
    if key not in MODEL_CONFIG:
        raise KeyError(f"Model config key '{key}' not found. "
                     f"Available: {list(MODEL_CONFIG.keys())}")
    return MODEL_CONFIG[key]