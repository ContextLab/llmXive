"""
Configuration module for the flight delay distribution analysis pipeline.

This module defines global constants for random seeds, data sources,
target parameters, and system limits.

IMPORTANT: Per FR-014 and Plan Phase 2, `x_min` is NOT defined here.
It must be estimated dynamically via KS minimization at runtime.
"""

import os
import re
from typing import Final, Optional

# Random Seed for reproducibility
RANDOM_SEED: Final[int] = 42

# BTS Data Source
# Canonical endpoint pattern for Bureau of Transportation Statistics (BTS) On-Time Performance data.
# The actual CSV files are named by year (e.g., On_Time_Data_2023.csv).
# We define the base URL and a helper to construct the year-specific URL.
BTS_BASE_URL: Final[str] = "https://transtats.bts.gov/PreProcessed_Data"

# Validation regex for the expected filename pattern
BTS_FILENAME_PATTERN: Final[str] = r"On_Time_Data_\d{4}\.csv"

def get_bts_url(year: Optional[int] = None) -> str:
    """
    Construct the full URL for the BTS On-Time Performance CSV for a specific year.

    Args:
        year: The target year. If None, uses TARGET_YEAR.

    Returns:
        The full URL string.

    Raises:
        ValueError: If the year is invalid (not 4 digits or out of reasonable range).
    """
    target = year if year is not None else TARGET_YEAR

    # Validate year
    if not isinstance(target, int) or target < 1987 or target > 2030:
        raise ValueError(f"Invalid target year: {target}. Must be between 1987 and 2030.")

    filename = f"On_Time_Data_{target}.csv"
    
    # Validate filename pattern (defensive)
    if not re.match(BTS_FILENAME_PATTERN, filename):
        raise ValueError(f"Generated filename '{filename}' does not match expected pattern.")

    return f"{BTS_BASE_URL}/{filename}"

# Target Year for analysis (default to current year - 1, or a fixed historical year for testing)
# This can be overridden by environment variable BTS_TARGET_YEAR
# Validation is performed in get_bts_url, but we ensure the default is reasonable here.
_default_year = int(os.getenv("BTS_TARGET_YEAR", "2023"))
if _default_year < 1987 or _default_year > 2030:
    # Fallback if env var is garbage, though get_bts_url will catch it later.
    # For config purity, we just store the raw env value or default, 
    # relying on the getter for strict validation.
    pass
TARGET_YEAR: Final[int] = _default_year

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