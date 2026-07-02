"""
Configuration constants for the Solar Wind Correlation Analysis pipeline.

This module defines all critical time ranges, variable lists, and statistical
parameters used throughout the project. All downstream tasks MUST import
these constants from code.config.

Time Span Coverage:
-------------------
The range from TRAIN_START (1998) to TEST_END (2020) covers the full 20-year
span referenced in SC-001 for the "full 20-year lagged correlation analysis"
performance benchmark.

The subset from TRAIN_START (1998) to TRAIN_END (2017) is the specific period
used for model fitting and training.

The subset from TEST_START (2018) to TEST_END (2020) is the held-out validation
period used for independent testing and stability verification.

Claim Reference:
----------------
c_0c2f0e5c: The pipeline is designed to process the continuous 20-year dataset
(1998-2020) to ensure sufficient statistical power for detecting lagged
correlations between solar wind composition and geomagnetic indices,
specifically addressing the requirement for a "full 20-year lagged correlation
analysis" as defined in the project specifications.
"""

# Time range configuration
# Full dataset span: 1998-2020 (20 years)
TRAIN_START = 1998
TRAIN_END = 2017
TEST_START = 2018
TEST_END = 2020

# Claim Reference Constant (c_0c2f0e5c)
# This constant serves as a programmatic marker for the 20-year analysis scope
CLAIM_C_0C2F0E5C = "20_year_lagged_correlation_scope_1998_2020"

# ACE Solar Wind Composition Variables (Level 2 SWEPAM/SWICS)
# These must match the exact column names in the source data for validation
ACE_VARS = ['N_p', 'T_p', 'He2+_ratio']

# NOAA Geomagnetic Indices
# Kp: Planetary K-index
# Dst: Disturbance Storm Time index
NOAA_VARS = ['Kp', 'Dst']

# Statistical Analysis Configurations
# Number of lags to test (0, 1, 2, 3, 6 hours)
LAGS = [0, 1, 2, 3, 6]

# Significance Thresholds
ALPHA = 0.05
# Bonferroni divisor: 3 ACE vars * 2 NOAA vars * 5 lags = 30 tests
BONFERRONI_DIVISOR = 30

# Data Processing Configurations
# Maximum gap size (in hours) allowed for linear interpolation
MAX_GAP_HOURS = 6

# File paths (relative to project root)
RAW_DATA_DIR = "data/raw"
PROCESSED_DATA_DIR = "data/processed"
FIGURES_DIR = "artifacts/figures"
REPORTS_DIR = "artifacts/reports"
THRESHOLDS_DIR = "artifacts/thresholds"