"""
Configuration module for the flight delay distribution analysis pipeline.

This module defines global constants for random seeds, data sources,
target parameters, and system limits.

IMPORTANT: Per FR-014 and Plan Phase 2, `x_min` is NOT defined here.
It must be estimated dynamically via KS minimization at runtime.
"""

import os
from typing import Final

# Random Seed for reproducibility
RANDOM_SEED: Final[int] = 42

# BTS Data Source
# Canonical endpoint for Bureau of Transportation Statistics (BTS) On-Time Performance data.
# This URL points to the public FTP/HTTP archive for the specific year.
BTS_URL: Final[str] = (
    "https://transtats.bts.gov/PreProcessed_Data/On_Time_Reporting_Carrier_On_Time_Performance_1987_present.json"
)
# Alternative direct CSV download pattern for specific year if JSON is not preferred,
# but the task implies a canonical endpoint. We will use a standard HTTP fetchable URL.
# Note: In production, this might need to be updated to the specific CSV generation endpoint
# or a local cache path if the direct API changes.
# For the purpose of this implementation, we define the base URL pattern.
BTS_BASE_URL: Final[str] = "https://transtats.bts.gov/PreProcessed_Data"

# Target Year for analysis (default to current year - 1, or a fixed historical year for testing)
# This can be overridden by environment variable BTS_TARGET_YEAR
TARGET_YEAR: Final[int] = int(os.getenv("BTS_TARGET_YEAR", "2023"))

# Memory Limit
# Maximum RAM allowed for processing in Gigabytes.
# Set to 6.5 GB as per specification.
MEMORY_LIMIT_GB: Final[float] = 6.5

# File Paths
# Root directory for data artifacts
DATA_DIR: Final[str] = "data"
RAW_DATA_DIR: Final[str] = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR: Final[str] = os.path.join(DATA_DIR, "processed")
RESULTS_DIR: Final[str] = os.path.join(DATA_DIR, "results")
LOGS_DIR: Final[str] = os.path.join(DATA_DIR, "logs")
FIGURES_DIR: Final[str] = "figures"

# Ensure directories exist (optional utility, but config usually just defines paths)
# We do not create them here to keep config pure, but we define the paths.

# Thresholds
# Note: X_MIN_THRESHOLD is intentionally NOT defined here.
# It is computed dynamically in code/models.py.

# Flight Delay Thresholds
FLIGHT_DELAY_ERROR_THRESHOLD: Final[int] = 10000  # Minutes
FLIGHT_DELAY_ANOMALY_THRESHOLD: Final[int] = 1440  # Minutes (24 hours)

# Retention Rate Threshold
MIN_RETENTION_RATE: Final[float] = 0.95

# Model Fitting Parameters
KS_MIN_GRID_SIZE: Final[int] = 100
VUONG_TEST_SIGNIFICANCE: Final[float] = 0.05

# Bootstrap Parameters
BOOTSTRAP_N_ITER: Final[int] = 1000
BOOTSTRAP_SIGIFICANCE: Final[float] = 0.1

# Hill Estimator Parameters
HILL_WINDOW_SIZE: Final[int] = 10
HILL_MAX_K_RATIO: Final[float] = 0.1  # k/n <= 0.1

# Runtime Limit
MAX_RUNTIME_SECONDS: Final[int] = 3600