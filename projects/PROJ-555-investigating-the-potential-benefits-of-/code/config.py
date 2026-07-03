"""
Configuration module for the Ecotourism Regeneration Analysis Pipeline.

This module defines constants, thresholds, and path configurations required
throughout the project. It serves as the single source of truth for
project-wide settings.
"""

import os
from pathlib import Path

# --- Project Root & Paths ---
# Determine the project root relative to this file (code/config.py)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directory Structure Constants
DIR_CODE = _PROJECT_ROOT / "code"
DIR_DATA = _PROJECT_ROOT / "data"
DIR_TESTS = _PROJECT_ROOT / "tests"
DIR_SPECS = _PROJECT_ROOT / "specs" / "001-ecotourism-regeneration"
DIR_FIGURES = _PROJECT_ROOT / "figures"

# Data Sub-directories
DIR_DATA_RAW = DIR_DATA / "raw"
DIR_DATA_PROCESSED = DIR_DATA / "processed"
DIR_DATA_ECOTOURISM = DIR_DATA / "ecotourism"
DIR_DATA_LANDSAT = DIR_DATA_RAW / "landsat"
DIR_DATA_CLIMATE = DIR_DATA_PROCESSED / "climate"

# Output Files
FILE_QUERY_LOG = DIR_DATA_RAW / "query_log.json"
FILE_SITE_COORDINATES = DIR_DATA_RAW / "site_coordinates.csv"
FILE_NDVI_TIMESERIES = DIR_DATA_PROCESSED / "ndvi_timeseries.parquet"
FILE_SITE_METADATA = DIR_DATA_PROCESSED / "site_metadata.csv"
FILE_CLIMATE_COVARIATES = DIR_DATA_PROCESSED / "climate_covariates.parquet"
FILE_RECOVERY_TRAJECTORIES = DIR_DATA_PROCESSED / "recovery_trajectories.parquet"
FILE_FINAL_REPORT = DIR_DATA_PROCESSED / "final_report.json"
FILE_SENSITIVITY_ANALYSIS = DIR_DATA_PROCESSED / "sensitivity_analysis.csv"
FILE_ECOTOURISM_REVENUE = DIR_DATA_ECOTOURISM / "revenue_data.csv"
FILE_ECOTOURISM_METADATA = DIR_DATA_ECOTOURISM / "metadata.json"
FILE_ECOTOURISM_PROCESSED = DIR_DATA_PROCESSED / "ecotourism_data.csv"

# --- NDVI & Deforestation Thresholds (FR-002, FR-001) ---
# NDVI is typically in range [-1, 1], but vegetation is usually [0, 1]
NDVI_MIN = -1.0
NDVI_MAX = 1.0
NDVI_VALID_MIN = 0.0  # Ignore non-vegetation (water, clouds, bare soil) for some analyses

# Deforestation Detection Thresholds
# FR-002: Deforestation defined as NDVI drop >= 0.30 sustained over 2 years
DEFORESTATION_DROP_THRESHOLD = 0.30
DEFORESTATION_DURATION_YEARS = 2
DEFORESTATION_DURATION_MONTHS = DEFORESTATION_DURATION_YEARS * 12

# Recovery Thresholds
# Minimum recovery period to be considered "complete" or "incomplete"
RECOVERY_PERIOD_MIN_YEARS = 5
RECOVERY_PERIOD_MIN_MONTHS = RECOVERY_PERIOD_MIN_YEARS * 12

# Model Fit Thresholds
# FR-002: R^2 >= 0.95 required for non-linear asymptotic model acceptance
MODEL_R2_THRESHOLD = 0.95

# Data Quality Thresholds
# Exclude sites with >50% data gaps
MAX_DATA_GAP_FRACTION = 0.50

# --- Memory & Performance Constraints (SC-005, FR-003) ---
# Target peak RAM usage limit (in GB)
TARGET_MAX_RAM_GB = 7.0
TARGET_MAX_RAM_BYTES = TARGET_MAX_RAM_GB * 1024**3

# Chunking parameters for streaming data to stay within RAM limits
# Estimated bytes per row for Landsat time series (approximate)
BYTES_PER_ROW_ESTIMATE = 1024  # 1KB per row estimate
# Calculate max rows per chunk to stay safely under limit (e.g., 80% of target)
SAFETY_FACTOR = 0.8
MAX_ROWS_PER_CHUNK = int((TARGET_MAX_RAM_BYTES * SAFETY_FACTOR) / BYTES_PER_ROW_ESTIMATE)

# --- Study Period ---
# Study period defined in plan.md/spec.md: 2000-2023
STUDY_START_YEAR = 2000
STUDY_END_YEAR = 2023

# --- API & Data Source Configuration ---
# Landsat Data Source
LANDSAT_PRODUCT_ID_PREFIX = "LE08"  # Landsat 8
LANDSAT_PRODUCT_ID_PREFIX_L9 = "LT09" # Landsat 9
LANDSAT_CLOUD_COVER_MAX = 30.0  # Max cloud cover percentage allowed

# Climate Data Sources
CHIRPS_PRODUCT = "CHIRPS_V2.0"
MODIS_PRODUCT = "MOD11A2"  # MODIS Land Surface Temperature

# --- Site Configuration ---
# Target number of paired sites (30 ecotourism + 30 control)
TARGET_SITE_COUNT = 30

# --- Revenue Thresholds for Sensitivity Analysis (FR-004, FR-007) ---
# Tiers for revenue sensitivity analysis
REVENUE_TIER_LOW = "low"
REVENUE_TIER_MEDIUM = "medium"
REVENUE_TIER_HIGH = "high"

# --- Logging Configuration ---
LOG_LEVEL_DEFAULT = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# --- Statistical Testing ---
# Significance level for hypothesis testing
ALPHA = 0.05
# Correction method for multiple comparisons (Bonferroni/Holm)
MULTIPLE_COMPARISON_METHOD = "holm"

def ensure_directories():
    """
    Creates all required data and output directories if they do not exist.
    Must be called before writing any files.
    """
    directories = [
        DIR_DATA_RAW,
        DIR_DATA_PROCESSED,
        DIR_DATA_ECOTOURISM,
        DIR_DATA_LANDSAT,
        DIR_FIGURES,
        DIR_TESTS,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

# Initialize directories on import (safe if they already exist)
try:
    ensure_directories()
except Exception:
    # Fail silently on import if permissions are an issue;
    # individual scripts should handle errors when writing.
    pass