"""
Configuration management for the Network Topology and Neural Synchrony project.

This module centralizes all project-wide constants and configuration parameters
required for data acquisition, preprocessing, and analysis.
"""

from pathlib import Path
from typing import Final

# Project Root (derived from the location of this file)
_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT: Final[Path] = _ROOT

# Data Paths
DATA_RAW_DIR: Final[Path] = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR: Final[Path] = PROJECT_ROOT / "data" / "processed"
FIGURES_DIR: Final[Path] = PROJECT_ROOT / "data" / "figures"

# --- Core Parameters (as specified in T007) ---

# OpenNeuro Dataset ID
# Source: OpenNeuro ds000246 (HCP-style task data)
OPENNEURO_ID: Final[str] = "ds000246"

# Number of subjects to process
# Per spec amendment T009a: N=30 to fit within 2GB disk constraints
N_SUBJECTS: Final[int] = 30

# Frame Displacement Threshold for motion exclusion (mm)
# Subjects with mean FD > this value will be excluded
FD_THRESHOLD: Final[float] = 0.5

# MNI Template Space
# Canonical template for spatial normalization
MNI_TEMPLATE: Final[str] = "MNI152NLin2009cAsym"

# Default Proportional Threshold for Graph Construction
# Used for binarizing/connecting the adjacency matrix (0.20 = top 20% edges)
THRESHOLD_DEFAULT: Final[float] = 0.20

# --- Derived Configuration ---

# Memory Guard Limit (RSS in GB)
# Hard limit enforced by memory_guard.py
MEMORY_LIMIT_GB: Final[float] = 6.5

# Preprocessing Parameters
TEMPORAL_FILTER_HIGH: Final[float] = 0.01  # Hz
TEMPORAL_FILTER_LOW: Final[float] = 0.1   # Hz

# Atlas Configuration
ATLAS_NAME: Final[str] = "Schaefer_200Parcels_7Networks"
N_REGIONS: Final[int] = 200

# Analysis Thresholds for Sensitivity Sweep (T028)
THRESHOLD_SWEEP_VALUES: Final[list[float]] = [0.10, 0.20, 0.30]

# --- Validation ---

def validate_config() -> None:
    """
    Validates that critical directories exist and parameters are within expected ranges.
    Raises ValueError if configuration is invalid.
    """
    if not (0 < N_SUBJECTS <= 100):
        raise ValueError(f"N_SUBJECTS ({N_SUBJECTS}) must be between 1 and 100.")
    if not (0.0 < THRESHOLD_DEFAULT < 1.0):
        raise ValueError(f"THRESHOLD_DEFAULT ({THRESHOLD_DEFAULT}) must be between 0 and 1.")
    if not (0.0 < FD_THRESHOLD < 1.0):
        raise ValueError(f"FD_THRESHOLD ({FD_THRESHOLD}) must be between 0 and 1.")

    # Ensure directories exist (create if missing)
    for d in [DATA_RAW_DIR, DATA_PROCESSED_DIR, FIGURES_DIR]:
        d.mkdir(parents=True, exist_ok=True)

# Run validation on import to catch errors early
validate_config()
