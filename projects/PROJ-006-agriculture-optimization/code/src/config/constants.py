"""
Configuration constants for the Climate-Smart Agriculture Optimization project.

This module centralizes all magic numbers, paths, and thresholds used across
the pipeline to ensure consistency and ease of maintenance.
"""

import os
from pathlib import Path

# Project Root
# Dynamically determine the project root based on the module's location
_CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _CURRENT_DIR.parent.parent.parent

# Data Paths
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_LOGS_DIR = DATA_DIR / "logs"
DATA_REMOTE_SENSING_DIR = DATA_RAW_DIR / "sentinel2"

# Output Paths
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

# Logging
LOGS_DIR = DATA_LOGS_DIR
LOG_FILE = LOGS_DIR / "pipeline_execution.log"

# Random Seeds
# Fixed seed for reproducibility of synthetic data and random splits
RANDOM_SEED = 42
NUMPY_SEED = 42

# Spatial Configuration
# Buffer size (km) around household coordinates to handle privacy fuzzing
# and match with satellite pixels
BUFFER_SIZE_KM = 1.0

# Grid resolution (km) for deriving village IDs from coordinates
GRID_RESOLUTION_KM = 0.1

# Satellite & Remote Sensing Thresholds
# Cloud cover thresholds for Sentinel-2 data quality filtering
CLOUD_COVER_LOW = 0.10
CLOUD_COVER_MEDIUM = 0.30
CLOUD_COVER_HIGH = 0.60
CLOUD_COVER_VERY_HIGH = 0.90

# Threshold used for initial data inclusion (exclude very high cloud cover)
CLOUD_COVER_THRESHOLD_DEFAULT = 0.95

# NDVI Configuration
# Minimum NDVI value considered valid (below this might be water/cloud shadow)
NDVI_MIN_VALID = -0.2
# Maximum NDVI value (theoretical max is 1.0)
NDVI_MAX_VALID = 1.0

# Statistical Analysis Configuration
# Significance level for hypothesis testing
ALPHA_BASE = 0.05

# VIF (Variance Inflation Factor) threshold for detecting multicollinearity
# Values > 5 indicate potential collinearity issues
VIF_THRESHOLD = 5.0

# Minimum sample size required for robust statistical inference
MIN_SAMPLE_SIZE = 300

# Linkage threshold: minimum percentage of households that must be successfully
# linked to satellite data to avoid aggregation
LINKAGE_THRESHOLD_PERCENT = 95.0

# File Extensions
EXTENSION_CSV = ".csv"
EXTENSION_PARQUET = ".parquet"
EXTENSION_JSON = ".json"
EXTENSION_YAML = ".yaml"
EXTENSION_TIF = ".tif"
EXTENSION_PNG = ".png"
EXTENSION_PDF = ".pdf"

# Contract Paths
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
DATASET_SCHEMA_PATH = CONTRACTS_DIR / "dataset.schema.yaml"
OUTPUT_SCHEMA_PATH = CONTRACTS_DIR / "output.schema.yaml"

# Configuration for Synthetic Data Generation (Structural Validation Mode)
# Used when real data is unavailable (T010)
SYNTHETIC_DATA_ROWS = 500
SYNTHETIC_COUNTRIES = ["Malawi", "Tanzania"]
SYNTHETIC_YEARS = [2015, 2016, 2017, 2018, 2019]

# Growth Season Months (simplified mapping for major crops in target regions)
# Format: Country -> List of months (1-12)
GROWING_SEASONS = {
    "Malawi": [3, 4, 5, 6, 7, 8, 9, 10],
    "Tanzania": [2, 3, 4, 5, 10, 11, 12, 1, 2],
    "Default": [3, 4, 5, 6, 7, 8, 9, 10]
}

# CSA Practice Weights (optional, for weighted CSA Index if needed)
# Currently using simple sum, but weights can be applied here
PRACTICE_WEIGHTS = {
    "practice_mixed_farming": 1.0,
    "practice_terracing": 1.0,
    "practice_conservation_tillage": 1.0,
    "practice_agroforestry": 1.0
}

# Environment Variable Flags
ENV_CI = "CI"
ENV_USE_REAL_DATA = "USE_REAL_DATA"
ENV_NO_SYNTHETIC = "NO_SYNTHETIC"