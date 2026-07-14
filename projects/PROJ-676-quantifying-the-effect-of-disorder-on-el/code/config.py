"""
Configuration module for the project.

Defines hyperparameters, random seeds, and path constants.
"""

import os
from pathlib import Path
from typing import Dict, Any

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW = DATA_DIR / "raw"
DATA_PROCESSED = DATA_DIR / "processed"
DATA_METADATA = DATA_DIR / "metadata"

# Output directories
FIGURES_DIR = PROJECT_ROOT / "figures"
DOCS_DIR = PROJECT_ROOT / "docs"

# Hyperparameters
DEFAULT_SEED = 42
NUM_REALIZATIONS = 100  # Per width
SYSTEM_SIZES = [100, 200, 400, 800, 1600]
DISORDER_WIDTHS = [0.5, 1.0, 2.0, 4.0, 8.0]

# Eigenvalue solver settings
EIGENVALUE_CONVERGENCE_THRESHOLD = 1e-8
MAX_EIGENVALUES = 100  # For sparse solvers, if used

# Memory limits (in bytes)
MEMORY_LIMIT_BYTES = 6 * 1024**3  # 6 GB

# Paths
PROVENANCE_FILE = DATA_METADATA / "provenance.json"
RESIDUALS_FILE = DATA_METADATA / "residuals.json"

def get_config() -> Dict[str, Any]:
    """
    Return a dictionary of configuration values.

    Returns:
        Dictionary of config values.
    """
    return {
        'PROJECT_ROOT': str(PROJECT_ROOT),
        'DATA_DIR': str(DATA_DIR),
        'DATA_RAW': str(DATA_RAW),
        'DATA_PROCESSED': str(DATA_PROCESSED),
        'DATA_METADATA': str(DATA_METADATA),
        'FIGURES_DIR': str(FIGURES_DIR),
        'DOCS_DIR': str(DOCS_DIR),
        'DEFAULT_SEED': DEFAULT_SEED,
        'NUM_REALIZATIONS': NUM_REALIZATIONS,
        'SYSTEM_SIZES': SYSTEM_SIZES,
        'DISORDER_WIDTHS': DISORDER_WIDTHS,
        'EIGENVALUE_CONVERGENCE_THRESHOLD': EIGENVALUE_CONVERGENCE_THRESHOLD,
        'MAX_EIGENVALUES': MAX_EIGENVALUES,
        'MEMORY_LIMIT_BYTES': MEMORY_LIMIT_BYTES,
        'PROVENANCE_FILE': str(PROVENANCE_FILE),
        'RESIDUALS_FILE': str(RESIDUALS_FILE),
    }
