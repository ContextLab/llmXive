"""
Configuration module for the Sensory Deprivation Network Dynamics project.

Defines all required directory paths and pipeline constants.
Directories are created on demand using ``llmxive_toolkit.paths.ensure_dir``.
"""

from pathlib import Path
from llmxive_toolkit import paths

# ----------------------------------------------------------------------
# Base data/result directories (relative to the project root)
# ----------------------------------------------------------------------
DATA_ROOT = Path("data")
RESULTS_DIR = Path("results")

# ----------------------------------------------------------------------
# Sub‑directories for each processing stage
# ----------------------------------------------------------------------
RAW_DIR = DATA_ROOT / "raw"
PREPROC_DIR = DATA_ROOT / "preprocessed"
QUALITY_DIR = DATA_ROOT / "quality"
CONNECTIVITY_DIR = DATA_ROOT / "connectivity"

# Ensure the directories exist when this module is imported
paths.ensure_dir(RAW_DIR)
paths.ensure_dir(PREPROC_DIR)
paths.ensure_dir(QUALITY_DIR)
paths.ensure_dir(CONNECTIVITY_DIR)
paths.ensure_dir(RESULTS_DIR)

# ----------------------------------------------------------------------
# Quality‑control thresholds
# ----------------------------------------------------------------------
FD_THRESHOLD = 0.5               # Framewise Displacement threshold (mm)
FD_VOLUME_PCT = 0.10             # Maximum proportion of high‑motion volumes

# Compatibility aliases used by legacy code
HIGH_MOTION_PERCENTAGE_THRESHOLD = FD_VOLUME_PCT

# ----------------------------------------------------------------------
# Dataset and analysis parameters
# ----------------------------------------------------------------------
DATASET_IDS = ["ds001770", "ds003820"]
MAX_SUBJECTS = 24
PERMUTATIONS = 1000
RANDOM_SEED = 42

# ----------------------------------------------------------------------
# Atlas configuration
# ----------------------------------------------------------------------
# Pin a specific release of the Schaefer‑400 atlas (example URL)
ATLAS_URL = (
    "https://github.com/ThomasYeoLab/CBIG/releases/download/"
    "v0.17.0/Schaefer2018_400Parcels_7Networks_order.txt"
)
ATLAS_CACHE_DIR = DATA_ROOT / "atlas_cache"
paths.ensure_dir(ATLAS_CACHE_DIR)

# ----------------------------------------------------------------------
# Helper paths used by other modules
# ----------------------------------------------------------------------
# Compatibility with existing scripts
RAW_DATA_DIR = RAW_DIR
PREPROC_DATA_DIR = PREPROC_DIR
QUALITY_MANIFEST_PATH = QUALITY_DIR / "exclusion_manifest.json"

# Optional external tool paths (set to ``None`` if not available)
BIDS_VALIDATOR_PATH = None  # e.g., Path("bids-validator") if installed

# Disk‑quota used by ``code/main.py`` (GB)
DISK_QUOTA_GB = 14

# ----------------------------------------------------------------------
# Miscellaneous constants
# ----------------------------------------------------------------------
# Minimum number of subjects required after quality control
MIN_SAMPLE_SIZE = 20

# Checkpoint file used by the pipeline orchestrator
CHECKPOINT_PATH = Path("data") / ".checkpoint.json"

# End of configuration file.