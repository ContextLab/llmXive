"""
Configuration constants for the plant trait SDM project.
"""
import os
from typing import Final

# Random Seeds
RANDOM_SEED: Final[int] = 42
N_SPLITS: Final[int] = 5

# Model Hyperparameters
MAX_DEPTH: Final[int] = 10
N_ESTIMATORS: Final[int] = 100

# Data Paths
DATA_DIR: Final[str] = "data"
PROCESSED_DIR: Final[str] = "data/processed"
RAW_DIR: Final[str] = "data/raw"
RESULTS_DIR: Final[str] = "results"

# Trait Configuration
REQUIRED_TRAITS: Final[list] = ["sla", "seed_mass", "plant_height"]
TRAIT_SOURCES: Final[dict] = {
    "handbook": "Handbook 2013",
    "public": "TRY Public Subset"
}

# Thresholds
SPATIAL_THINNING_KM: Final[float] = 10.0
MIN_THINNING_KM: Final[float] = 1.0
VIF_THRESHOLD: Final[float] = 5.0

# Background Sampling
# Note: The exact number is deferred in the spec, so we set a placeholder.
# This should be updated based on the specific species or user input.
BACKGROUND_POINTS_PER_SPECIES: Final[int] = 1000

# Logging
LOG_LEVEL: Final[str] = "INFO"

# Protocol Constants
HANDBOOK_2013_SOURCE: Final[str] = "Handbook 2013"
UNVERIFIED_PROTOCOL_FLAG: Final[str] = "unverified protocol"