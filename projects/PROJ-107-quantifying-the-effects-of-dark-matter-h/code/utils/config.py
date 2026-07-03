"""
Configuration management for the Dark Matter Halo Shape Analysis pipeline.

This module provides:
- Path constants relative to the project root.
- A deterministic random seed for reproducibility.
- Environment-aware configuration loading.
"""
import os
import random
from pathlib import Path
from typing import Any, Dict

import yaml

# --- Path Constants ---
# Determine the project root (parent of the 'code' directory)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_CODE_ROOT = _PROJECT_ROOT / "code"
_DATA_ROOT = _PROJECT_ROOT / "data"
_DATA_RAW = _DATA_ROOT / "raw"
_DATA_PROCESSED = _DATA_ROOT / "processed"
_DATA_MILLIENNIUM = _DATA_RAW / "millennium"
_FIGURES_ROOT = _PROJECT_ROOT / "figures"
_SPEC_ROOT = _PROJECT_ROOT / "specs"

# Ensure directories exist
_DATA_RAW.mkdir(parents=True, exist_ok=True)
_DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
_DATA_MILLIENNIUM.mkdir(parents=True, exist_ok=True)
_FIGURES_ROOT.mkdir(parents=True, exist_ok=True)


# --- Deterministic Seed ---
# Fixed seed for reproducibility across runs as per task requirements
RANDOM_SEED = 42

# Apply seed immediately for numpy (if available) and standard library
try:
    import numpy as np
    np.random.seed(RANDOM_SEED)
except ImportError:
    pass

random.seed(RANDOM_SEED)


# --- Configuration Loader ---
def load_config(config_path: str = "data/metadata.yaml") -> Dict[str, Any]:
    """
    Load configuration from a YAML file.

    Args:
        config_path: Relative path from project root to the config file.

    Returns:
        Dictionary containing configuration parameters.

    Raises:
        FileNotFoundError: If the config file does not exist.
    """
    full_path = _PROJECT_ROOT / config_path
    if not full_path.exists():
        # Return a default minimal config if metadata.yaml is missing
        # This allows the pipeline to start even before T007 creates the file.
        return {
            "version": "0.1.0",
            "random_seed": RANDOM_SEED,
            "paths": {
                "data_raw": str(_DATA_RAW),
                "data_processed": str(_DATA_PROCESSED),
            }
        }

    with open(full_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# --- Global Configuration Instance ---
# Load config on module import
CONFIG = load_config()

# --- Path Accessors ---
def get_data_raw_path() -> Path:
    """Return the path to the raw data directory."""
    return _DATA_RAW

def get_data_processed_path() -> Path:
    """Return the path to the processed data directory."""
    return _DATA_PROCESSED

def get_figures_path() -> Path:
    """Return the path to the figures directory."""
    return _FIGURES_ROOT

def get_millennium_path() -> Path:
    """Return the path to the Millennium-II data directory."""
    return _DATA_MILLIENNIUM

def get_project_root() -> Path:
    """Return the project root directory."""
    return _PROJECT_ROOT

# --- Constants for Processing ---
# Defined here for easy access across the pipeline
MIN_PARTICLES_PER_HALO = 10000
CHUNK_SIZE_DEFAULT = 1000  # Number of haloes per chunk
BONFERRONI_ALPHA = 0.05
TRIAXIALITY_THRESHOLDS = {
    "prolate": 0.5,
    "triaxial": 0.8,
    "spherical": 1.0
}

# Output file names
OUTPUT_HALO_SHAPES = "halo_shapes.csv"
OUTPUT_STATS_RESULTS = "statistical_results.csv"
OUTPUT_SENSITIVITY_REPORT = "sensitivity_report.csv"
OUTPUT_MILLENNIUM_RESULTS = "millennium_results.csv"
OUTPUT_ALIGNMENT_ANGLES = "alignment_angles.csv"
OUTPUT_METADATA = "metadata.yaml"

def get_output_path(filename: str) -> Path:
    """Construct a full path for an output file in the processed directory."""
    return _DATA_PROCESSED / filename

def get_raw_data_path(filename: str, subfolder: str = None) -> Path:
    """Construct a full path for a raw data file."""
    if subfolder:
        return _DATA_RAW / subfolder / filename
    return _DATA_RAW / filename