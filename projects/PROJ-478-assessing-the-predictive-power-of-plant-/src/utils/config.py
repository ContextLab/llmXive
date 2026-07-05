"""
Configuration constants and resource limits for the plant traits SDM pipeline.

This module centralizes hyperparameters, random seeds, and resource constraints
to ensure reproducibility and compliance with CPU-only runner limits.
"""
import os
from typing import Final

# Reproducibility
RANDOM_SEED: Final[int] = 42
"""Global random seed for all stochastic processes."""

# Resource Limits (CPU-only runner constraints)
MAX_DEPTH: Final[int] = 10
"""Maximum depth for Random Forest trees to prevent memory explosion."""

N_ESTIMATORS: Final[int] = 100
"""Number of trees in the Random Forest ensemble."""

# Spatial Processing Defaults
SPATIAL_THINNING_KM: Final[float] = 10.0
"""Default minimum distance (km) between occurrence records."""

MIN_THINNING_KM: Final[float] = 1.0
"""Minimum allowed thinning distance (km) to prevent over-filtering."""

# Model Evaluation Defaults
N_CV_FOLDS: Final[int] = 5
"""Number of folds for cross-validation."""

# Data Processing Constants
MIN_RECORDS_PER_SPECIES: Final[int] = 10
"""Minimum number of occurrence records required to train a model."""

# File Paths (Relative to project root)
DATA_RAW_DIR: Final[str] = "data/raw"
DATA_PROCESSED_DIR: Final[str] = "data/processed"
DATA_METADATA_DIR: Final[str] = "data/metadata"
RESULTS_DIR: Final[str] = "results"
SRC_DIR: Final[str] = "src"

# Logging Configuration
LOG_LEVEL: Final[str] = "INFO"
LOG_FORMAT: Final[str] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE: Final[str] = "pipeline.log"

# External Data Sources
WORLDCCLIM_VERSION: Final[str] = "2.1"
WORLDCCLIM_RESOLUTION: Final[str] = "30s"
GBIF_API_BASE: Final[str] = "https://api.gbif.org/v1"
TRY_DB_VERSION: Final[str] = "2023-01"

# Statistical Analysis Constants
VIF_THRESHOLD: Final[float] = 5.0
"""Variance Inflation Factor threshold for multicollinearity flagging."""

P_VALUE_THRESHOLD: Final[float] = 0.05
"""Standard alpha level for statistical significance."""

SENSITIVITY_THRESHOLDS: Final[list] = [0.01, 0.02, 0.05]
"""Thresholds for sensitivity analysis sweep."""

SENSITIVITY_CONSISTENCY_TARGET: Final[float] = 0.67
"""Target consistency rate (2 out of 3) for sensitivity analysis."""