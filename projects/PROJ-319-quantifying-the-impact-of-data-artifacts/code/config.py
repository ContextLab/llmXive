"""
Configuration module for the llmXive project: Quantifying the Impact of Data Artifacts.

This module centralizes all project constants, including:
- Pinned random seeds for reproducibility (FR-008)
- Default directory paths relative to the project root
- Concrete artifact parameters for noise and saturation sweeps (FR-002, FR-003, SC-003)
"""

import os
from pathlib import Path
from typing import List, Tuple

# ============================================================================
# Reproducibility: Pinned Random Seeds
# ============================================================================
# FR-008: All stochastic processes must use a deterministic seed.
GLOBAL_SEED: int = 42
SYNTHETIC_SEED: int = 1234
NOISE_SEED: int = 5678
SATURATION_SEED: int = 9012

# ============================================================================
# Project Paths
# ============================================================================
# Derived dynamically to ensure portability, but defaults to the standard layout.
# T001a created these directories; this config assumes they exist.

def _get_project_root() -> Path:
    """
    Returns the project root directory.
    Assumes the script is run from the repository root or code/ directory.
    """
    # Try to find 'code' directory upwards from current file location
    current_file = Path(__file__).resolve()
    root = current_file.parent.parent
    
    # Verify it looks like a project root (contains expected folders)
    if not (root / "data").exists() and not (root / "tests").exists():
        # Fallback if running from a different context
        root = Path(os.getcwd())
        
    return root

PROJECT_ROOT: Path = _get_project_root()

# Directory Paths
DIR_CODE: Path = PROJECT_ROOT / "code"
DIR_DATA_RAW: Path = PROJECT_ROOT / "data" / "raw"
DIR_DATA_SYNTHETIC: Path = PROJECT_ROOT / "data" / "synthetic"
DIR_DATA_PROCESSED: Path = PROJECT_ROOT / "data" / "processed"
DIR_DATA_VALIDATION: Path = PROJECT_ROOT / "data" / "validation"
DIR_TESTS_UNIT: Path = PROJECT_ROOT / "tests" / "unit"
DIR_TESTS_CONTRACT: Path = PROJECT_ROOT / "tests" / "contract"
DIR_TESTS_INTEGRATION: Path = PROJECT_ROOT / "tests" / "integration"
DIR_LOGS: Path = PROJECT_ROOT / "logs"
DIR_FIGURES: Path = PROJECT_ROOT / "figures"

# File Paths (Defaults)
GT_METADATA_FILE: Path = DIR_DATA_SYNTHETIC / "gt_metadata.json"
NOISE_SWEEP_DIR: Path = DIR_DATA_PROCESSED / "noise_sweeps"
SATURATION_SWEEP_FILE: Path = DIR_DATA_PROCESSED / "saturation_sweep.csv"
STATS_RESULTS_FILE: Path = DIR_LOGS / "stats_results.csv"
RESEARCH_LOG_FILE: Path = DIR_LOGS / "research.log"
CALIBRATION_FUNCTIONS_FILE: Path = DIR_DATA_PROCESSED / "calibration_functions.json"

# ============================================================================
# Artifact Parameters (Concrete Values)
# ============================================================================
# Derived from spec assumptions on typical instrumental variations.
# These values are used by code/synthetic/artifacts.py for sweep generation.

# Noise Levels (FR-002)
# Ranges from low to moderate noise relative to median signal.
# Values represent the multiplier of the median signal intensity.
NOISE_LEVELS: List[float] = [0.01, 0.05, 0.10]

# Saturation Range (FR-003, SC-003)
# Range: 0.0 (baseline) to 0.5 (50% of brightest pixels clipped)
# Step: 0.05 increments
SATURATION_FRACTIONS: List[float] = [
    0.00, 0.05, 0.10, 0.15, 0.20,
    0.25, 0.30, 0.35, 0.40, 0.45, 0.50
]

# ============================================================================
# Image Generation Defaults (for synthetic generation)
# ============================================================================
IMAGE_SIZE: int = 128  # Pixels (square)
NEBULA_CORE_RADIUS: float = 10.0  # Pixels
NEBULA_SHELL_RADIUS: float = 30.0  # Pixels
BASE_INTENSITY: float = 1000.0  # Arbitrary units (ADU)

# ============================================================================
# Statistical Test Parameters
# ============================================================================
# FR-005: Statistical significance threshold
ALPHA: float = 0.05
BONFERRONI_CORRECTION: bool = True

# ============================================================================
# Logging Configuration
# ============================================================================
LOG_LEVEL: str = "INFO"
LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"