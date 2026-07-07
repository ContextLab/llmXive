import os
from pathlib import Path

# Project root based on the file location (code/src/config.py)
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
CODE_DIR = PROJECT_ROOT / "code"
SRC_DIR = PROJECT_ROOT / "code" / "src"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Quality Control Thresholds
# Framewise Displacement threshold in mm (SC-004)
FD_THRESHOLD = 0.5

# Percentage of volumes allowed to exceed FD threshold
HIGH_MOTION_PERCENTAGE_THRESHOLD = 0.10

# Minimum sample size required to proceed (SC-004)
MIN_SAMPLE_SIZE = 20

# Dataset IDs
DATASET_IDS = ["ds001770", "ds003820"]

# Atlas settings
ATLAS_VERSION = "c_dea14405"
ATLAS_NAME = "Schaefer2018_400Parcels_7Networks"
ATLAS_URL = "https://raw.githubusercontent.com/ThomasYeoLab/CBIG/v1.0.0/stable_projects/brain_parcellation/Schaefer2018_LocalGlobal/Parcels/MNI152_Schaefer2018_400Parcels_7Networks_order.txt"
ATLAS_CACHE_DIR = DATA_DIR / "atlas_cache"
ATLAS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
