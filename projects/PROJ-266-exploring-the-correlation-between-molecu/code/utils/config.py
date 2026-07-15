"""
Configuration module for the molecular flexibility and permeability project.

This module centralizes random seeds, file paths, and constant parameters
to ensure reproducibility and consistency across the pipeline.
"""

import os
import random
from pathlib import Path
from typing import Dict, Any

# Project Root
# Assumes the code structure: project_root/code/utils/config.py
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Directory Paths
DATA_DIR = _PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
FIGURES_DIR = _PROJECT_ROOT / "figures"
SPECS_DIR = _PROJECT_ROOT / "specs" / "001-molecular-flexibility-permeability"
CONTRACTS_DIR = SPECS_DIR / "contracts"

# Ensure directories exist (for initialization scripts)
# Note: Do not auto-create in production runs unless explicitly intended.
# These paths are provided for reference in other modules.

# Random Seeds for Reproducibility
# Set these to ensure deterministic behavior in RDKit, numpy, etc.
RANDOM_SEED = 42
RDKit_SEED = 42
NUMPY_SEED = 42

# Constants
# Conformer generation settings (per Plan.md Deviation DEV-001)
# Overrides Spec FR-003 (50 conformers) for CPU feasibility.
MAX_CONFORMERS = 20
MMFF_MAX_ITER = 200
RMSD_CUTOFF = 0.5  # Angstroms

# Data Processing
MIN_RECORDS_TARGET = 500
MIN_RAW_BATCH_SIZE = 600
CHENMBL_ASSAY_TYPE = "Caco-2"
CHENMBL_STANDARD_TYPE = "MEASUREMENT"

# Statistical Analysis
ALPHA_FDR = 0.05  # Benjamini-Hochberg q-value threshold
VIF_THRESHOLD = 5.0  # Variance Inflation Factor threshold for collinearity
IQR_MULTIPLIER = 1.5  # Outlier detection multiplier

# ChEMBL API Settings
CHEMBL_BASE_URL = "https://www.ebi.ac.uk/chembl/ws"
API_TIMEOUT = 30  # seconds
MAX_RETRIES = 5
RETRY_BACKOFF_FACTOR = 2

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def get_project_root() -> Path:
    """Return the project root directory."""
    return _PROJECT_ROOT

def set_seed(seed: int = RANDOM_SEED) -> None:
    """
    Set random seeds for reproducibility across the stack.

    Args:
        seed: The integer seed to use. Defaults to RANDOM_SEED.
    """
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    try:
        import rdkit
        rdkit.RDConfig.RANDOM_SEED = seed
        # Note: RDKit seed setting is often done via specific functions
        # or environment variables depending on the version.
        # This is a best-effort global setting.
    except ImportError:
        pass

def get_config_summary() -> Dict[str, Any]:
    """
    Return a summary of the current configuration for logging.

    Returns:
        A dictionary containing key configuration values.
    """
    return {
        "project_root": str(_PROJECT_ROOT),
        "data_dir": str(DATA_DIR),
        "random_seed": RANDOM_SEED,
        "max_conformers": MAX_CONFORMERS,
        "min_records_target": MIN_RECORDS_TARGET,
        "vif_threshold": VIF_THRESHOLD,
        "alpha_fdr": ALPHA_FDR,
    }