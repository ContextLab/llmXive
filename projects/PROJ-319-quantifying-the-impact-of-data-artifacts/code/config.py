"""
Project configuration: seeds, paths, and concrete artifact parameters.
This module defines all global constants required for reproducibility and
experiment configuration, adhering to FR-002, FR-003, and SC-003.
"""
import os
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

# Project Root
# Determine root relative to this file (project root is parent of code/)
_ROOT = Path(__file__).parent.parent
if not (_ROOT / "tasks.md").exists():
    # Fallback if config is moved or run from different context
    _ROOT = Path.cwd()

def get_project_root() -> Path:
    """Return the project root directory path."""
    return _ROOT

# Paths
DATA_RAW = _ROOT / "data" / "raw"
DATA_SYNTHETIC = _ROOT / "data" / "synthetic"
DATA_PROCESSED = _ROOT / "data" / "processed"
DATA_VALIDATION = _ROOT / "data" / "validation"
LOGS_DIR = _ROOT / "logs"

# Random Seeds (Constitution Principle: Reproducibility)
# Fixed seeds to ensure deterministic results across runs
GLOBAL_SEED = 42
NOISE_SEED = 42
GENERATOR_SEED = 12345
SATURATION_SEED = 56789

# Artifact Parameters (Concrete Values)
# Derived from T037a decision document: 0.0 to 0.5 in 0.05 increments
SATURATION_LEVELS: List[float] = [
    0.0, 0.05, 0.10, 0.15, 0.20, 0.25,
    0.30, 0.35, 0.40, 0.45, 0.50
]
"""
Saturation clipping fractions.
Ranges from 0.0 (no saturation) to 0.5 (50% of brightest pixels clipped)
in 0.05 increments. Defined in T037a and T037b.
"""

# Derived from FR-002: Noise levels {0.01, 0.05, 0.10}
# Expanded to a sweep for statistical power as per SC-003, but keeping the
# specific requested levels as the primary test set.
NOISE_LEVELS: List[float] = [0.01, 0.05, 0.10]
"""
Gaussian noise levels as a fraction of median signal.
Core levels defined in FR-002: {0.01, 0.05, 0.10}.
"""

# Extended noise levels for full sensitivity sweep (if required by specific analysis)
NOISE_LEVELS_FULL_SWEEP: List[float] = [
    0.01, 0.02, 0.03, 0.04, 0.05,
    0.06, 0.07, 0.08, 0.09, 0.10
]

# Image Parameters
IMAGE_SIZE: Tuple[int, int] = (256, 256)
"""Default synthetic image size (height, width)."""

# Default Number of Synthetic Images
DEFAULT_N_IMAGES: int = 50
"""Default number of synthetic planetary nebulae to generate (T006)."""

# Metric Thresholds
ELLIPTICITY_TOLERANCE: float = 1e-6
ASYMMETRY_TOLERANCE: float = 1e-6

# Statistical Parameters
SIGNIFICANCE_LEVEL: float = 0.05
BONFERRONI_ALPHA: float = 0.05
POWER_TARGET: float = 0.80
EFFECT_SIZE_SMALL: float = 0.2
EFFECT_SIZE_MEDIUM: float = 0.5
EFFECT_SIZE_LARGE: float = 0.8

# File Extensions
FITS_EXT = ".fits"
JSON_EXT = ".json"
CSV_EXT = ".csv"
LOG_EXT = ".log"
MD_EXT = ".md"

# Output File Names (Declared Deliverables)
GT_METADATA_FILE = "gt_metadata.json"
NOISE_TREND_REPORT = "noise_trend_report.csv"
NOISE_STATS_FILE = "noise_stats.csv"
SATURATION_SWEEP_FILE = "saturation_sweep.csv"
SATURATION_STATS_FILE = "saturation_stats.csv"
CALIBRATION_FUNCTIONS_FILE = "calibration_functions.json"
RUN_MANIFEST_FILE = "run_manifest.json"
POWER_ANALYSIS_REPORT = "power_analysis_report.md"
VALIDATION_REPORT = "validation_report.md"
VALIDATION_MANIFEST = "validation_manifest.json"

def get_config_summary() -> Dict[str, Any]:
    """Return a dictionary of all configuration parameters for logging/manifests."""
    return {
        "global_seed": GLOBAL_SEED,
        "noise_seed": NOISE_SEED,
        "generator_seed": GENERATOR_SEED,
        "saturation_seed": SATURATION_SEED,
        "noise_levels": NOISE_LEVELS,
        "saturation_levels": SATURATION_LEVELS,
        "image_size": IMAGE_SIZE,
        "default_n_images": DEFAULT_N_IMAGES,
        "paths": {
            "raw": str(DATA_RAW),
            "synthetic": str(DATA_SYNTHETIC),
            "processed": str(DATA_PROCESSED),
            "validation": str(DATA_VALIDATION),
            "logs": str(LOGS_DIR)
        }
    }