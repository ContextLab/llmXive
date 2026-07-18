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
# The file MUST be placed here manually before execution.
HCP_MMP_FILE_PATH: Final[str] = "raw/HCP_MMP1.0_Glasser2016.zip"

# SHA-256 Hash of the pinned HCP-MMP parcellation file.
# This hash MUST match the file placed in data/raw/HCP_MMP1.0_Glasser2016.zip.
# If the file is missing or hash mismatch, the pipeline will fail loudly.
# NOTE: This is a placeholder. The actual hash must be calculated from the real file
# once it is placed in the repository. For now, we use a dummy hash that will cause
# a failure if the file is not correctly placed and hashed by the user/setup script.
# In a real scenario, this would be the SHA-256 of the official Glasser2016 HCP-MMP file.
# Since we cannot fetch the file here, we assume the user has placed it and we calculate
# the hash in a setup script (T005) or we use a known constant if the file is standard.
# For the purpose of this implementation, we set a placeholder that will trigger the error
# if the file is not present or has a different hash.
# The user/setup process (T004/T005) is responsible for ensuring the file is present and
# updating this constant or calculating it dynamically if the file is present.
# However, per T004, we define it as a constant.
# We will use a placeholder hash that is unlikely to match any real file to force the
# user to update it or ensure the file is present and the hash is calculated correctly.
# In a real deployment, this would be the actual hash.
# Let's use a dummy value that will fail, forcing the user to fix it.
HCP_MMP_HASH: Final[str] = "0" * 64  # Placeholder: Must be updated with real hash

# --- Sensitivity Thresholds (T004, T031) ---
# Hardcoded list of thresholds for sensitivity analysis as per Spec.
SENSITIVITY_THRESHOLDS: Final[tuple] = (0.70, 0.75, 0.80)

# --- Logging Configuration ---
LOG_LEVEL: Final[str] = "INFO"
LOG_FORMAT: Final[str] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# --- Research Phase Config (T025b) ---
# Default minimum sample size for the routing gate (T029c)
N_MIN_DEFAULT: Final[int] = 10

# --- Hyperparameters (Example) ---
RANDOM_SEED: Final[int] = 42
MAX_ITERATIONS: Final[int] = 1000

# Ensure directories exist on import (optional, can be called explicitly)
# ensure_directories()
