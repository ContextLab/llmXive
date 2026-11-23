"""
Configuration module for the planetary nebula artifact analysis pipeline.

This module provides:
* Helper functions to locate the project root.
* A summary of the current configuration.
* All constant values required by the other modules (generator,
  artifact injection, statistical analysis, etc.).
"""

import os
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict, Any

# ----------------------------------------------------------------------
# Project‑root helper
# ----------------------------------------------------------------------
def get_project_root() -> Path:
    """
    Return the absolute path to the project root directory.

    The function assumes it resides somewhere inside the ``code/`` package
    and walks two directories up to reach the repository root.
    """
    return Path(__file__).resolve().parents[2]

# ----------------------------------------------------------------------
# Configuration summary (placeholder – can be expanded later)
# ----------------------------------------------------------------------
def get_config_summary() -> Dict[str, Any]:
    """
    Return a dictionary summarising the current configuration.

    This is a lightweight helper used by logging / reproducibility
    utilities.  At the moment it only reports the random seed and the
    image size, but additional fields can be added as the pipeline
    evolves.
    """
    return {
        "random_seed": RANDOM_SEED,
        "image_size": IMAGE_SIZE,
    }

# ----------------------------------------------------------------------
# Core constant definitions required by the pipeline
# ----------------------------------------------------------------------
# Random seed used throughout the synthetic generation and artifact
# injection modules.  Chosen arbitrarily but fixed for reproducibility.
RANDOM_SEED: int = 42

# Seed used specifically for noise‑injection unit tests.
NOISE_SEED: int = 2021

# Default full‑width‑half‑maximum (FWHM) of the Gaussian nebula
# (in pixel units).  The value is realistic for the synthetic images
# used in the project.
DEFAULT_FWHM: float = 5.0

# Allowed ranges for ground‑truth ellipticity and asymmetry.
# Values are inclusive and chosen to produce a diverse synthetic set.
ELLIPTICITY_RANGE: Tuple[float, float] = (0.0, 0.9)
ASYMMETRY_RANGE: Tuple[float, float] = (0.0, 0.5)

# Image dimensions for all synthetic FITS files.
IMAGE_SIZE: Tuple[int, int] = (256, 256)

# Filename for the ground‑truth JSON manifest written by the
# synthetic generator.
GT_METADATA_FILE: str = "gt_metadata.json"

# ----------------------------------------------------------------------
# Artifact‑injection parameters (used by the CLI and unit tests)
# ----------------------------------------------------------------------
DEFAULT_NOISE_LEVELS: List[float] = [0.01, 0.05, 0.10]  # σ as fraction of median
DEFAULT_SATURATION_FRACTIONS: List[float] = [
    round(i * 0.05, 2) for i in range(0, 11)
]  # 0.0 … 0.5 in 0.05 steps

# ----------------------------------------------------------------------
# Paths / filenames used by the statistical‑analysis modules
# ----------------------------------------------------------------------
DATA_PROCESSED: Path = Path("data") / "processed"
NOISE_STATS_FILE: str = "noise_stats.csv"
SATURATION_STATS_FILE: str = "saturation_stats.csv"

# ----------------------------------------------------------------------
# Public API of this module
# ----------------------------------------------------------------------
__all__ = [
    "get_project_root",
    "get_config_summary",
    "RANDOM_SEED",
    "NOISE_SEED",
    "DEFAULT_FWHM",
    "ELLIPTICITY_RANGE",
    "ASYMMETRY_RANGE",
    "IMAGE_SIZE",
    "GT_METADATA_FILE",
    "DEFAULT_NOISE_LEVELS",
    "DEFAULT_SATURATION_FRACTIONS",
    "DATA_PROCESSED",
    "NOISE_STATS_FILE",
    "SATURATION_STATS_FILE",
]
