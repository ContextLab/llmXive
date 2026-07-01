"""
Configuration constants and resource limits for the plant traits SDM pipeline.

This module centralizes all hyperparameters, random seeds, and resource constraints
to ensure reproducibility and consistency across the project.
"""

import os
from typing import Final

# ============================================================================
# Random Seeds for Reproducibility
# ============================================================================
# Fixed seed for all random number generation (NumPy, Python random, sklearn, etc.)
RANDOM_SEED: Final[int] = 42

# Seed for specific operations if needed separately (currently using global seed)
NUMPY_SEED: Final[int] = RANDOM_SEED
SKLEARN_SEED: Final[int] = RANDOM_SEED

# ============================================================================
# Model Hyperparameters (Resource Limits for CPU-only runners)
# ============================================================================
# Random Forest constraints to prevent memory overflow on CPU-only environments
MAX_DEPTH: Final[int] = 10
N_ESTIMATORS: Final[int] = 100

# Additional RF parameters
MIN_SAMPLES_SPLIT: Final[int] = 2
MIN_SAMPLES_LEAF: Final[int] = 1
MAX_FEATURES: Final[str] = "sqrt"

# ============================================================================
# Data Processing Parameters
# ============================================================================
# Spatial thinning distance (in km) - default as per spec
SPATIAL_THINNING_DISTANCE_KM: Final[float] = 10.0
MIN_SPATIAL_THINNING_DISTANCE_KM: Final[float] = 1.0

# Background sampling
# Note: The actual number of background points is deferred to spec/plan
# This constant serves as a placeholder for the logic implementation
BACKGROUND_POINTS_DEFERRED: Final[bool] = True

# ============================================================================
# Statistical Analysis Parameters
# ============================================================================
# Significance level for hypothesis testing
ALPHA: Final[float] = 0.05

# Variance Inflation Factor threshold for multicollinearity
VIF_THRESHOLD: Final[float] = 5.0

# Sensitivity analysis thresholds for thinning distance
SENSITIVITY_THRESHOLDS_KM: Final[tuple] = (0.01, 0.02, 0.05)

# Minimum consistency rate for sensitivity analysis (2 out of 3 = 67%)
SENSITIVITY_CONSISTENCY_THRESHOLD: Final[float] = 0.67

# ============================================================================
# File Paths and Directories
# ============================================================================
# Base directory (project root)
BASE_DIR: Final[str] = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Data directories
DATA_RAW_DIR: Final[str] = os.path.join(BASE_DIR, "data", "raw")
DATA_PROCESSED_DIR: Final[str] = os.path.join(BASE_DIR, "data", "processed")
DATA_METADATA_DIR: Final[str] = os.path.join(BASE_DIR, "data", "metadata")

# Results directories
RESULTS_DIR: Final[str] = os.path.join(BASE_DIR, "results")
FIGURES_DIR: Final[str] = os.path.join(RESULTS_DIR, "figures")

# Source directories
SRC_DIR: Final[str] = os.path.join(BASE_DIR, "src")
MODELING_DIR: Final[str] = os.path.join(SRC_DIR, "modeling")
ANALYSIS_DIR: Final[str] = os.path.join(SRC_DIR, "analysis")
DATA_DIR: Final[str] = os.path.join(SRC_DIR, "data")
UTILS_DIR: Final[str] = os.path.join(SRC_DIR, "utils")

# ============================================================================
# External Data Sources
# ============================================================================
# GBIF API configuration
GBIF_BASE_URL: Final[str] = "https://api.gbif.org/v1"
GBIF_OCCURRENCE_ENDPOINT: Final[str] = f"{GBIF_BASE_URL}/occurrence/search"

# WorldClim configuration
WORLDCCLIM_VERSION: Final[str] = "2.1"
WORLDCCLIM_BASE_URL: Final[str] = "https://bio-clim.org"

# TRY Database configuration
TRY_PUBLIC_SUBSET_URL: Final[str] = "https://www.try-db.org/TryWeb/Data.php"
TRY_DATA_HANDBOOK_2013: Final[str] = "Handbook 2013"

# ============================================================================
# Performance and Resource Limits
# ============================================================================
# Maximum memory usage (in MB) for data loading
MAX_MEMORY_MB: Final[int] = 4096

# Number of CPU workers for parallel operations (set to 1 for reproducibility if needed)
N_WORKERS: Final[int] = -1  # -1 means use all available cores

# Timeout for API requests (in seconds)
REQUEST_TIMEOUT: Final[int] = 30

# ============================================================================
# Species Configuration
# ============================================================================
# Default focal species for MVP (User Story 1)
DEFAULT_FOCAL_SPECIES: Final[str] = "Helianthus annuus"

# Target number of species for community-level analysis (User Story 3)
TARGET_SPECIES_COUNT: Final[int] = 50

# ============================================================================
# Logging and Provenance
# ============================================================================
# Log file name
LOG_FILE_NAME: Final[str] = "pipeline_provenance.log"

# Provenance tracking enabled
PROVENANCE_TRACKING_ENABLED: Final[bool] = True

# ============================================================================
# Validation Flags
# ============================================================================
# Strict mode: fail on any data quality issue
STRICT_MODE: Final[bool] = False

# Enable debug logging
DEBUG_MODE: Final[bool] = False