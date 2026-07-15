"""
Project configuration: seeds, paths, and concrete artifact parameters.
"""
import os
from pathlib import Path
from typing import List, Tuple

# Project Root
_ROOT = Path(__file__).parent.parent
if not (_ROOT / "tasks.md").exists():
    # Fallback if config is moved
    _ROOT = Path.cwd()

# Paths
DATA_RAW = _ROOT / "data" / "raw"
DATA_SYNTHETIC = _ROOT / "data" / "synthetic"
DATA_PROCESSED = _ROOT / "data" / "processed"
DATA_VALIDATION = _ROOT / "data" / "validation"
LOGS_DIR = _ROOT / "logs"

# Random Seeds (Constitution Principle: Reproducibility)
GLOBAL_SEED = 42
NOISE_SEED = 42
GENERATOR_SEED = 12345

# Artifact Parameters (Concrete Values)
# Derived from spec assumptions on typical instrumental variations
NOISE_LEVELS: List[float] = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10]
"""
Gaussian noise levels as a fraction of median signal.
Ranges from low (0.01) to moderate (0.10).
"""

SATURATION_LEVELS: List[float] = [
    0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50
]
"""
Saturation clipping fractions.
Ranges from 0.0 (no saturation) to 0.5 (50% of brightest pixels clipped)
in 0.05 increments.
"""

# Image Parameters
IMAGE_SIZE: Tuple[int, int] = (256, 256)
"""Default synthetic image size (height, width)."""

# Metric Thresholds
ELLIPTICITY_TOLERANCE: float = 1e-6
ASYMMETRY_TOLERANCE: float = 1e-6