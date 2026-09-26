"""
Project configuration constants and resource limits.

This module provides centralized configuration values used throughout the project,
including random seeds, model hyperparameters, and resource constraints.
"""
import os
from typing import Final

# Random seeds for reproducibility
RANDOM_SEED: Final[int] = 42
NEST_SEED: Final[int] = 42

# Model hyperparameters (CPU-optimized)
MAX_DEPTH: Final[int] = 10
N_ESTIMATORS: Final[int] = 100
MIN_SAMPLES_SPLIT: Final[int] = 5
MIN_SAMPLES_LEAF: Final[int] = 2

# Cross-validation settings
N_FOLDS: Final[int] = 5

# Data processing settings
SPATIAL_THINNING_KM: Final[float] = 10.0
MIN_SPATIAL_THINNING_KM: Final[float] = 1.0
BACKGROUND_POINTS_DEFERRED: Final[int] = 10000  # Placeholder, to be configured

# Variance Inflation Factor threshold
VIF_THRESHOLD: Final[float] = 5.0

# Sensitivity analysis thresholds
SENSITIVITY_THRESHOLDS: Final[list] = [0.01, 0.02, 0.05]
SENSITIVITY_CONSISTENCY_THRESHOLD: Final[float] = 0.67  # 67%

# File paths
DATA_RAW_DIR: Final[str] = "data/raw"
DATA_PROCESSED_DIR: Final[str] = "data/processed"
DATA_METADATA_DIR: Final[str] = "data/metadata"
RESULTS_DIR: Final[str] = "results"

# Logging
LOG_LEVEL: Final[str] = os.getenv("LOG_LEVEL", "INFO")
PROVENANCE_FILE: Final[str] = "provenance.json"

# Checksum verification
CHECKSUM_ALGORITHM: Final[str] = "sha256"
MANIFEST_FILENAME: Final[str] = "download_manifest.json"

# Species list for analysis (can be overridden via config)
FOCAL_SPECIES: Final[list] = [
    "Helianthus_annuus",
    "Zea_mays",
    "Glycine_max",
    "Triticum_aestivum",
    "Oryza_sativa"
]

# Trait columns
REQUIRED_TRAITS: Final[list] = ["SLA", "seed_mass", "plant_height"]

# Climate variables (WorldClim v2.1)
CLIMATE_VARIABLES: Final[list] = [
    "bio1", "bio2", "bio3", "bio4", "bio5", "bio6", "bio7", "bio8",
    "bio9", "bio10", "bio11", "bio12", "bio13", "bio14", "bio15",
    "bio16", "bio17", "bio18", "bio19"
]
