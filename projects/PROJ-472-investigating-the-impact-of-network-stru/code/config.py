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
# Relative path to the parcellation file, resolved against the project root.
HCP_MMP_FILE_PATH: Final[str] = "data/raw/HCP_MMP1.0_Glasser2016.zip"

# URL for the HCP-MMP parcellation file (Human Connectome Project).
HCP_MMP_URL: Final[str] = "https://www.humanconnectome.org/storage/app/media/documentation/s1200/HCP_MMP1.0_Glasser2016.zip"

# SHA-256 of the pinned HCP-MMP parcellation zip.
# No upstream hash is hard-coded here: the hash of the file actually
# downloaded is computed at runtime and recorded in
# data/processed/parcellation_hash.json; on every subsequent run the
# computed hash is compared against that recorded value, so any change
# to the parcellation file fails loudly instead of being silently
# accepted. An empty string means "not yet pinned".
HCP_MMP_HASH: Final[str] = ""

# --- Sensitivity Thresholds (T004, T031) ---
# Fixed list of avalanche-detection thresholds for the sensitivity sweep.
SENSITIVITY_THRESHOLDS: Final[tuple] = (0.70, 0.75, 0.80)

# --- Logging Configuration ---
LOG_LEVEL: Final[str] = "INFO"
LOG_FORMAT: Final[str] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# --- Research Phase Config ---
# Minimum sample size for the routing gate (T029c).
N_MIN: Final[int] = 10

# --- Hyperparameters ---
# RNG seed pinned for all stochastic steps (permutation shuffling etc.).
RANDOM_SEED: Final[int] = 42
MAX_ITERATIONS: Final[int] = 1000
