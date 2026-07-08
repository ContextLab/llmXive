"""
Configuration management for the Statistical Analysis of Cognitive Decline project.

This module centralizes project paths, random seeds, and hardware constraints
(CPU-only execution) to ensure reproducibility and consistent behavior across
the pipeline.
"""

import os
import random
from pathlib import Path
from typing import Any, Dict

import numpy as np
import yaml

# ============================================================================
# Project Root and Directory Constants
# ============================================================================

# Determine project root based on the location of this file (code/config.py)
# This ensures paths work regardless of the current working directory when
# the script is invoked.
_CURRENT_FILE_PATH = Path(__file__).resolve()
PROJECT_ROOT = _CURRENT_FILE_PATH.parent.parent
PROJECT_ROOT = PROJECT_ROOT if PROJECT_ROOT.name != "code" else PROJECT_ROOT.parent

# Standardized directory structure as per T001
DIRS = {
    "root": PROJECT_ROOT,
    "code": PROJECT_ROOT / "code",
    "data": PROJECT_ROOT / "data",
    "data_raw": PROJECT_ROOT / "data" / "raw",
    "data_processed": PROJECT_ROOT / "data" / "processed",
    "data_interim": PROJECT_ROOT / "data" / "interim",
    "data_results": PROJECT_ROOT / "data" / "results",
    "tests": PROJECT_ROOT / "tests",
    "specs": PROJECT_ROOT / "specs",
    "figures": PROJECT_ROOT / "figures",
}

# ============================================================================
# Random Seeds for Reproducibility
# ============================================================================

# Default seed value. Changing this affects all random operations.
DEFAULT_SEED = 42

# Global seed state
_seed = DEFAULT_SEED

def set_seed(seed: int) -> None:
    """
    Set the random seed for Python, NumPy, and any other relevant libraries.
    This ensures reproducibility of experiments.
    """
    global _seed
    _seed = seed
    random.seed(seed)
    np.random.seed(seed)

    # If torch is available (optional dependency), set its seed too
    # We wrap in try/except to avoid hard dependency on torch if not installed
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

def get_seed() -> int:
    """Get the currently configured random seed."""
    return _seed

# Initialize seed immediately on import
set_seed(DEFAULT_SEED)

# ============================================================================
# Hardware Constraints (CPU-Only)
# ============================================================================

# Force CPU-only execution as per project constraints
FORCE_CPU = True

def get_device() -> str:
    """
    Return the device string ('cpu' or 'cuda').
    Enforces CPU-only constraint regardless of hardware availability.
    """
    return "cpu"

def get_max_workers() -> int:
    """
    Return the maximum number of workers for parallel processing.
    Limits to 4 to prevent memory exhaustion on standard machines.
    """
    import multiprocessing
    return min(4, multiprocessing.cpu_count())

# ============================================================================
# Data Source Configuration
# ============================================================================

class DataSourceConfig:
    """Configuration for external data sources."""

    # Primary source: ADReSS Challenge
    # URL for the ADReSS dataset (GitHub release or canonical location)
    # Note: This is a placeholder URL; the actual download logic in ingestion.py
    # should fetch the specific archive.
    ADRESS_URL = "https://github.com/mc556/ADReSS/raw/main/ADReSS_data.zip"
    ADRESS_CHECKSUM_FILE = DIRS["data_raw"] / "checksums.json"

    # DementiaBank is explicitly excluded as a primary source per plan.md
    # and T012c. It is only available as a fallback if ADReSS fails.
    DEMENTIABANK_URL = None  # Disabled by default
    DEMENTIABANK_ENABLED = False

    @classmethod
    def get_primary_source(cls) -> Dict[str, Any]:
        return {
            "name": "ADReSS",
            "url": cls.ADRESS_URL,
            "checksum_file": str(cls.ADRESS_CHECKSUM_FILE),
        }

# ============================================================================
# Model and Feature Configuration
# ============================================================================

class ModelConfig:
    """Configuration for machine learning models and embeddings."""

    # Semantic embedding model (CPU-optimized)
    EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION = 384

    # Statistical testing parameters
    ALPHA = 0.05
    BONFERRONI_ADJUSTMENT = True

    # Memory constraints
    MAX_MEMORY_GB = 7.0
    BATCH_SIZE = 16  # Small batch size for CPU memory safety

# ============================================================================
# Path Resolvers
# ============================================================================

def get_path(key: str) -> Path:
    """
    Retrieve a configured directory path by key.
    Raises KeyError if the key is not found.
    """
    if key not in DIRS:
        raise KeyError(f"Unknown directory key: {key}. Valid keys: {list(DIRS.keys())}")
    return DIRS[key]

def ensure_dirs() -> None:
    """Create all standard directories if they do not exist."""
    for path in DIRS.values():
        if isinstance(path, Path):
            path.mkdir(parents=True, exist_ok=True)

# ============================================================================
# Configuration Loading/Saving (Optional Utility)
# ============================================================================

def save_config(filepath: Path) -> None:
    """
    Save the current configuration state to a YAML file.
    Useful for logging the exact environment of a run.
    """
    config = {
        "seed": get_seed(),
        "device": get_device(),
        "max_workers": get_max_workers(),
        "data_source": DataSourceConfig.get_primary_source(),
        "embedding_model": ModelConfig.EMBEDDING_MODEL_NAME,
        "max_memory_gb": ModelConfig.MAX_MEMORY_GB,
    }
    with open(filepath, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False)

def load_config(filepath: Path) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    Note: This does not automatically re-set seeds or device flags unless
    explicitly called.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Config file not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# ============================================================================
# Initialization
# ============================================================================

# Ensure directories exist upon import
# This is safe to run multiple times
ensure_dirs()