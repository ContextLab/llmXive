"""
Project configuration module.

This module defines project‑wide constants used across the codebase.
Values can be overridden via environment variables, enabling flexible
configuration without code changes.
"""
from pathlib import Path
import os

# ----------------------------------------------------------------------
# Project root
# ----------------------------------------------------------------------
# The directory containing this file is <project_root>/code
# PROJECT_ROOT therefore is two levels up from this file's location.
PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]

# ----------------------------------------------------------------------
# Core experiment parameters (already used in other modules)
# ----------------------------------------------------------------------
TARGET_N: int = int(os.getenv("TARGET_N", "4000"))
ALPHA: float = float(os.getenv("ALPHA", "0.05"))
EFFECT_SIZE_D: float = float(os.getenv("EFFECT_SIZE_D", "0.5"))
MIN_GROUP_SIZE: int = int(os.getenv("MIN_GROUP_SIZE", "30"))

# ----------------------------------------------------------------------
# Dataset identifiers
# ----------------------------------------------------------------------
# The default Hugging Face dataset that provides Reddit comments.
# Can be overridden with the environment variable DATASET_NAME.
DATASET_NAME: str = os.getenv(
    "DATASET_NAME", "fddemarco/pushshift-reddit-comments"
)
# Dataset split to use; typically "train". Override with DATASET_SPLIT.
DATASET_SPLIT: str = os.getenv("DATASET_SPLIT", "train")
# Whether to use streaming mode; defaults to True for large datasets.
DATASET_STREAMING: bool = os.getenv("DATASET_STREAMING", "true").lower() in (
    "true",
    "1",
    "yes",
)

# ----------------------------------------------------------------------
# Output directory configuration
# ----------------------------------------------------------------------
# Base data directory (relative to project root). Can be changed via
# DATA_ROOT env var (useful for custom storage locations).
DATA_ROOT: Path = Path(os.getenv("DATA_ROOT", "data"))

# Sub‑directories for the various pipeline stages.
RAW_DATA_DIR: Path = DATA_ROOT / os.getenv("RAW_DATA_SUBDIR", "raw")
PROCESSED_DATA_DIR: Path = DATA_ROOT / os.getenv("PROCESSED_DATA_SUBDIR", "processed")
VALIDATION_DATA_DIR: Path = DATA_ROOT / os.getenv("VALIDATION_DATA_SUBDIR", "validation")
RESULTS_DIR: Path = Path(os.getenv("RESULTS_DIR", "results"))
FIGURES_DIR: Path = Path(os.getenv("FIGURES_DIR", "figures"))

# Ensure that the directories exist when the module is imported.
# The llmxive_toolkit `paths` helpers also create directories on demand,
# but having them created here guarantees that any code that constructs
# paths manually will not fail.
for _dir in (
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    VALIDATION_DATA_DIR,
    RESULTS_DIR,
    FIGURES_DIR,
):
    _dir.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# Exported names (for static analysis / IDEs)
# ----------------------------------------------------------------------
__all__ = [
    "PROJECT_ROOT",
    "TARGET_N",
    "ALPHA",
    "EFFECT_SIZE_D",
    "MIN_GROUP_SIZE",
    "DATASET_NAME",
    "DATASET_SPLIT",
    "DATASET_STREAMING",
    "DATA_ROOT",
    "RAW_DATA_DIR",
    "PROCESSED_DATA_DIR",
    "VALIDATION_DATA_DIR",
    "RESULTS_DIR",
    "FIGURES_DIR",
]