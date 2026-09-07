"""
Configuration constants for the Agriculture Optimization project.

This module defines all hard-coded configuration values used across the pipeline,
including random seeds, file paths, spatial parameters, and analysis thresholds.
"""
import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Directories
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_LOGS_DIR = DATA_DIR / "logs"
DATA_REMOTE_SENSING_DIR = DATA_RAW_DIR / "sentinel2"

REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

SPECS_DIR = PROJECT_ROOT / "specs" / "001-climate-smart-eval"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

# Random Seeds
RANDOM_SEED = 42
NP_RANDOM_SEED = 42
TORCH_RANDOM_SEED = 42  # For future ML components

# Spatial Configuration
# Buffer size in kilometers for geodesic buffering around household coordinates
# Used to handle LSMS-ISA privacy fuzzing and ensure pixel coverage
BUFFER_SIZE_KM = 1.0

# Grid resolution in kilometers for village ID derivation
# Used to cluster households into village-level units
GRID_RESOLUTION_KM = 0.1

# Cloud Cover Thresholds for Sentinel-2 data filtering
# Low cloud cover: < 0.2 (20%)
CLOUD_COVER_LOW_THRESHOLD = 0.2

# Medium cloud cover: 0.2 to 0.6 (20% - 60%)
CLOUD_COVER_MEDIUM_THRESHOLD = 0.6

# High cloud cover: >= 0.8 (80%) - typically excluded from analysis
CLOUD_COVER_HIGH_THRESHOLD = 0.8

# Very high cloud cover: >= 0.95 (95%) - strictly excluded
CLOUD_COVER_VERY_HIGH_THRESHOLD = 0.95

# Default cloud cover threshold for initial data ingestion
DEFAULT_CLOUD_COVER_THRESHOLD = 0.8

# Analysis Parameters
# Minimum linkage percentage required to avoid village-level aggregation
MIN_LINKAGE_PERCENTAGE = 95.0

# Minimum sample size required to avoid village-level aggregation
MIN_SAMPLE_SIZE = 300

# Statistical Analysis Parameters
# Significance level for hypothesis testing
ALPHA = 0.05

# Bonferroni correction: adjusted alpha will be calculated as ALPHA / num_tests
# Default number of tests for initial calculation (will be updated dynamically)
DEFAULT_NUM_TESTS = 20

# Variance Inflation Factor (VIF) threshold for collinearity warning
VIF_WARNING_THRESHOLD = 5.0

# Outlier detection threshold (number of standard deviations from mean)
OUTLIER_STD_THRESHOLD = 3.0

# NDVI Time-series Parameters
# Minimum number of observations required for stability score calculation
MIN_NDVI_OBSERVATIONS = 3

# NDVI validity range (normalized difference vegetation index)
NDVI_MIN_VALID = -1.0
NDVI_MAX_VALID = 1.0

# File Formats
CSV_EXTENSION = ".csv"
PARQUET_EXTENSION = ".parquet"
JSON_EXTENSION = ".json"
YAML_EXTENSION = ".yaml"
TIFF_EXTENSION = ".tif"
PNG_EXTENSION = ".png"
PDF_EXTENSION = ".pdf"

# Log Levels
DEFAULT_LOG_LEVEL = "INFO"
VALID_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# Pipeline Stages
PIPELINE_STAGE_INGEST = "ingest"
PIPELINE_STAGE_ANALYSIS = "analysis"
PIPELINE_STAGE_FULL = "full"

# Validation Schema Types
SCHEMA_TYPE_DATASET = "dataset"
SCHEMA_TYPE_REGRESSION = "regression"
SCHEMA_TYPE_SENSITIVITY = "sensitivity"

# Output File Names
SURVEY_RAW_FILE = "survey_raw.csv"
SURVEY_FILTERED_FILE = "filtered_survey.csv"
SPATIAL_JOINED_FILE = "spatial_joined_data.csv"
RAW_NDVI_TIMESERIES_FILE = "raw_ndvi_timeseries.parquet"
FEATURE_ENGINEERED_FILE = "feature_engineered_data.csv"
ANALYSIS_DATASET_FILE = "analysis_dataset.csv"
ANALYSIS_DATASET_AGGREGATED_FILE = "analysis_dataset_village_aggregated.csv"
LINKAGE_VALIDATION_FILE = "linkage_validation.json"
REGRESSION_RESULTS_FILE = "regression_results.json"
SENSITIVITY_RESULTS_FILE = "sensitivity_results.csv"
SENSITIVITY_METRICS_FILE = "sensitivity_metrics.json"
FINAL_REPORT_FILE = "final_report.pdf"
SENSITIVITY_PLOT_FILE = "sensitivity_plot.png"

# Log File Names
INGESTION_ERRORS_LOG = "ingestion_errors.log"
PIPELINE_LOG = "pipeline.log"

# Contract File Names
DATASET_SCHEMA_FILE = "dataset.schema.yaml"
REGRESSION_SCHEMA_FILE = "output.schema.yaml"

# Research Document
RESEARCH_DOCUMENT_PATH = SPECS_DIR / "research.md"

# Synthetic Data Configuration
SYNTHETIC_DATA_GENERATOR_FILE = "structural_validation_data.csv"
SYNTHETIC_DATA_ENABLED_ENV_VAR = "USE_SYNTHETIC_DATA"
CI_ENV_VAR = "CI"

# API and Data Source Configuration (placeholders for real data sources)
LSMS_ISA_AVAILABLE = False  # Real data unavailable, using synthetic/UCI fallback
SENTINEL2_AVAILABLE = False  # Real data unavailable, using synthetic proxy

# Time Series Configuration
GROWING_SEASON_MONTHS = {
    "ETH": [3, 4, 5, 6, 7, 8, 9, 10],  # Ethiopia
    "KEN": [3, 4, 5, 6, 7, 8, 9, 10],  # Kenya
    "MWI": [11, 12, 1, 2, 3, 4, 5],    # Malawi
    "UGA": [3, 4, 5, 6, 7, 8, 9, 10],  # Uganda
}

# Default country for growing season mapping if not specified
DEFAULT_COUNTRY = "ETH"