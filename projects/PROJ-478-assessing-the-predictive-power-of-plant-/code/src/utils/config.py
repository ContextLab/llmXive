import os
from typing import Final

# Random Seeds
RANDOM_SEED: Final[int] = 42
NEST_SEED: Final[int] = 42

# Resource Limits (CPU/Time constraints)
MAX_DEPTH: Final[int] = 10
N_ESTIMATORS: Final[int] = 100
MAX_MEMORY_MB: Final[int] = 4096
MAX_WORKERS: Final[int] = 4

# Data Paths
DATA_RAW_DIR: Final[str] = "data/raw"
DATA_PROCESSED_DIR: Final[str] = "data/processed"
DATA_METADATA_DIR: Final[str] = "data/metadata"
RESULTS_DIR: Final[str] = "results"

# Model Parameters
RF_PARAMS: Final[dict] = {
    "max_depth": MAX_DEPTH,
    "n_estimators": N_ESTIMATORS,
    "random_state": RANDOM_SEED,
    "n_jobs": MAX_WORKERS,
}

# Spatial Thinning
THINNING_DISTANCE_KM: Final[float] = 10.0
MIN_THINNING_DISTANCE_KM: Final[float] = 1.0

# Background Sampling
BACKGROUND_POINTS_PER_SPECIES: Final[int] = 10000  # Default, can be overridden

# Statistical Thresholds
VIF_THRESHOLD: Final[float] = 5.0
P_VALUE_THRESHOLD: Final[float] = 0.05
SENSITIVITY_THRESHOLDS: Final[list] = [0.01, 0.02, 0.05]
SENSITIVITY_CONSISTENCY_RATIO: Final[float] = 0.67
