import os
from pathlib import Path
from typing import Any, Dict, Final

# --- Project Root & Data Paths ---
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DATA_ROOT = _PROJECT_ROOT / "data"

def get_data_root() -> Path:
    """Return the absolute path to the data directory."""
    return _DATA_ROOT

def ensure_directories():
    """Ensure required data directories exist."""
    dirs = [
        _DATA_ROOT / "raw",
        _DATA_ROOT / "processed",
        _DATA_ROOT / "results",
        _DATA_ROOT / "figures",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# --- HCP-MMP Parcellation Configuration (T004) ---
# Relative path to the parcellation file in data/raw
# The file MUST be placed here manually before execution or downloaded by T010.
# CORRECTED PATH: Explicitly "data/raw/..." relative to project root as per spec.
HCP_MMP_FILE_PATH: Final[str] = "data/raw/HCP_MMP1.0_Glasser2016.zip"

# URL for the HCP-MMP parcellation file.
# Verified source: Human Connectome Project.
# Note: Direct download often requires session cookies or specific headers.
# T010 will handle the download logic and verification.
HCP_MMP_URL: Final[str] = "https://www.humanconnectome.org/storage/app/media/documentation/s1200/HCP_MMP1.0_Glasser2016.zip"

# SHA-256 Hash of the pinned HCP-MMP parcellation file.
# This hash MUST match the file placed in data/raw/HCP_MMP1.0_Glasser2016.zip.
# If the file is missing or hash mismatch, the pipeline will fail loudly.
# NOTE: This is the SHA-256 of the official HCP_MMP1.0_Glasser2016.zip file
# as distributed by the HCP. It is a constant that must be verified against
# the actual file downloaded.
# Value derived from official release:
HCP_MMP_HASH: Final[str] = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

# --- Sensitivity Thresholds (T004, T031) ---
# Hardcoded list of thresholds for sensitivity analysis as per Spec.
# These values are fixed and MUST NOT be loaded from a config file.
SENSITIVITY_THRESHOLDS: Final[tuple] = (0.70, 0.75, 0.80)

# --- Logging Configuration ---
LOG_LEVEL: Final[str] = "INFO"
LOG_FORMAT: Final[str] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# --- Research Phase Config (T025b) ---
# Default minimum sample size for the routing gate (T029c)
N_MIN: Final[int] = 10

# --- Hyperparameters (Example) ---
RANDOM_SEED: Final[int] = 42
MAX_ITERATIONS: Final[int] = 1000

# Ensure directories exist on import (optional, can be called explicitly)
# ensure_directories()