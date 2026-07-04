"""
Configuration module for the llmXive automated science pipeline.
Defines pinned random seeds, file paths, and utility functions for configuration management.
"""
import os
import random
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np

# --- Project Root ---
# Assume the project root is the parent of the 'code' directory
# or explicitly set if running from a specific environment.
# For robustness, we calculate it relative to this file.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# --- Random Seeds ---
RANDOM_SEED = 42
PERMUTATION_ITERATIONS = 1000

# --- Directory Paths (Relative to Project Root) ---
RAW_DATA_DIR = 'data/raw'
PROCESSED_DATA_DIR = 'data/processed'
FIGURES_DIR = 'figures'
LOGS_DIR = 'logs'

# --- Configuration Loading ---
def get_project_root() -> Path:
    """Returns the absolute path to the project root."""
    return _PROJECT_ROOT

def get_data_raw_path() -> Path:
    """Returns the absolute path to the raw data directory."""
    return get_project_root() / RAW_DATA_DIR

def get_data_processed_path() -> Path:
    """Returns the absolute path to the processed data directory."""
    return get_project_root() / PROCESSED_DATA_DIR

def get_data_figures_path() -> Path:
    """Returns the absolute path to the figures directory."""
    return get_project_root() / FIGURES_DIR

def get_logs_path() -> Path:
    """Returns the absolute path to the logs directory."""
    return get_project_root() / LOGS_DIR

def get_config_path() -> Path:
    """Returns the path to the config file if it exists."""
    return get_project_root() / 'config.yaml'

def load_config() -> Dict[str, Any]:
    """
    Loads configuration from a YAML file if it exists.
    Falls back to defaults if the file is missing.
    """
    import yaml
    config_path = get_config_path()
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f) or {}
    return {}

def get_config_value(key: str, default: Any = None) -> Any:
    """
    Retrieves a specific value from the configuration.
    """
    config = load_config()
    return config.get(key, default)

def set_seeds(seed: Optional[int] = None) -> None:
    """
    Pins the random seeds for reproducibility.
    
    Args:
        seed: Optional integer seed. If None, uses RANDOM_SEED from this module.
    """
    if seed is None:
        seed = RANDOM_SEED
    
    random.seed(seed)
    np.random.seed(seed)
    
    # RDKit seed setting (if available)
    try:
        from rdkit import RDConfig
        # RDKit uses a global seed for some operations
        # Note: RDKit's random seed handling can be version-dependent
        # This is the standard way to attempt seeding
        import rdkit
        # RDKit does not have a simple setSeed function exposed in all versions,
        # but setting the global random seed often propagates.
        # For strict reproducibility in RDKit, one might need to set environment variables
        # or specific flags depending on the version.
        # However, standard practice in pipelines is to set python/numpy seeds.
        # We attempt to set the RDKit random seed if the API exists.
        if hasattr(rdkit, 'Random'):
            rdkit.Random.seed(seed)
    except ImportError:
        pass

def get_config_summary() -> Dict[str, Any]:
    """
    Returns a dictionary containing the current configuration summary.
    Useful for logging and debugging.
    """
    return {
        'random_seed': RANDOM_SEED,
        'permutation_iterations': PERMUTATION_ITERATIONS,
        'raw_data_dir': RAW_DATA_DIR,
        'processed_data_dir': PROCESSED_DATA_DIR,
        'figures_dir': FIGURES_DIR,
        'logs_dir': LOGS_DIR,
        'project_root': str(get_project_root())
    }
