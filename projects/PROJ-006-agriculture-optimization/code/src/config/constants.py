"""
Configuration constants for the Agriculture Optimization project.

This module defines random seeds, file paths, and processing thresholds
used throughout the pipeline to ensure reproducibility and consistent behavior.
"""

import os
from pathlib import Path

# --- Random Seeds for Reproducibility ---
RANDOM_SEED = 42
"""Global random seed for numpy, pandas, and sklearn operations."""

NumpyRandomSeed = RANDOM_SEED
"""Alias for numpy random seed usage."""

# --- Project Paths ---
# Determine project root relative to this file (code/src/config/constants.py)
_ROOT_DIR = Path(__file__).resolve().parents[3]

PROJECT_ROOT = _ROOT_DIR
"""Root directory of the project."""

DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
"""Directory for raw, unprocessed data downloads."""

DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
"""Directory for cleaned and feature-engineered data."""

DATA_LOGS_DIR = PROJECT_ROOT / "data" / "logs"
"""Directory for execution logs and error reports."""

FIGURES_DIR = PROJECT_ROOT / "figures"
"""Directory for generated plots and visualizations."""

REPORTS_DIR = PROJECT_ROOT / "reports"
"""Directory for final reports and summaries."""

CONTRACTS_DIR = PROJECT_ROOT / "contracts"
"""Directory for schema contract definitions."""

CODE_DIR = PROJECT_ROOT / "code"
"""Root directory for source code (includes src/)."""

SRC_DIR = CODE_DIR / "src"
"""Source code directory."""

# --- Processing Thresholds ---
# Cloud cover thresholds for Sentinel-2 imagery filtering
# These values represent the maximum acceptable cloud cover percentage (0.0 to 1.0)
# to include a scene in the analysis.
CLOUD_COVER_THRESHOLDS = {0.6, 0.7, 0.8}
"""Set of cloud cover thresholds (0.0-1.0) for sensitivity analysis."""

DEFAULT_CLOUD_COVER_THRESHOLD = 0.7
"""Default cloud cover threshold used if not specified during processing."""

# --- Statistical Constants ---
ALPHA_BONFERRONI = 0.0167
"""Bonferroni-corrected alpha threshold (0.05 / 3 tests)."""

VIF_THRESHOLD = 5.0
"""Variance Inflation Factor threshold for flagging multicollinearity."""

MIN_SAMPLE_SIZE = 300
"""Minimum effective sample size required for statistical power."""

# --- File Extensions ---
EXT_CSV = ".csv"
EXT_PARQUET = ".parquet"
EXT_JSON = ".json"
EXT_YAML = ".yaml"
EXT_PNG = ".png"
EXT_PDF = ".pdf"

# --- Logging ---
LOG_FILE_NAME = "ingestion_errors.log"
"""Default name for the ingestion error log file."""

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
"""Standard logging format string."""

# --- Data Source Constants ---
# LSMS-ISA Country Codes
COUNTRY_CODE_MALAWI = "MWI"
COUNTRY_CODE_TANZANIA = "TZA"

# Sentinel-2 Processing Levels
SENTINEL2_LEVEL_L1C = "L1C"
SENTINEL2_LEVEL_L2A = "L2A"
DEFAULT_SENTINEL2_LEVEL = SENTINEL2_LEVEL_L2A

# --- API Configuration ---
# Copernicus Data Space Ecosystem
COPERNICUS_API_TIMEOUT = 30
"""Timeout in seconds for Copernicus API requests."""

COPERNICUS_MAX_RETRIES = 3
"""Maximum number of retries for failed API requests."""

# --- Vector/Spatial Constants ---
# Buffer distance in meters for spatial join fuzzing
SPATIAL_JOIN_BUFFER_METERS = 500
"""Buffer radius around household coordinates for pixel intersection."""

# --- Time Windows ---
# Growing season months by country (1-based)
GROWING_SEASON_MALAWI = [3, 4, 5]  # March, April, May
GROWING_SEASON_TANZANIA_MAIN = [3, 4, 5]  # Long rains
GROWING_SEASON_TANZANIA_ZANZIBAR = [3, 4, 5]  # Long rains

# --- Error Messages ---
ERROR_REAL_DATA_MISSING = (
    "Real data is missing and --synthetic flag was not set. "
    "Cannot proceed without real data or explicit synthetic override."
)
"""Error message for missing real data when synthetic fallback is disabled."""

ERROR_SCHEMA_MISMATCH = "Dataset schema validation failed."
"""Error message for schema validation failures."""