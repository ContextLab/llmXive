"""
Configuration constants for the Solar Wind Composition and Geomagnetic Indices project.

This module defines all project-wide constants including date ranges, variable names,
and verified data source URLs. All downstream tasks MUST import these constants from
this module.
"""

# Date Ranges
# TRAIN_START to TEST_END covers the full multi-decade span referenced in SC-001
# for the "full 20-year lagged correlation analysis" performance benchmark.
# TRAIN_START to TRAIN_END is the subset used for model fitting.
TRAIN_START = 1998
TRAIN_END = 2017
TEST_START = 2018
TEST_END = 2020

# ACE Variables (Level 2 SWEPAM/SWICS)
# These must match the raw column names exactly: 'N_p', 'T_p', 'He2+_ratio'
ACE_VARS = ['N_p', 'T_p', 'He2+_ratio']

# NOAA Variables (Kp, Dst indices)
NOAA_VARS = ['Kp', 'Dst']

# Verified Data Source URLs
# These URLs are the single source of truth for data acquisition.
# If these URLs are unreachable, the pipeline MUST fail loudly.
# ACE URL: FTP path to Level 2 data (SWEPAM/SWICS)
# Note: For HTTP access, a mirror or specific file path might be needed.
# We use the official NASA SPDF FTP path as the primary source.
ACE_URL = "ftp://spdf.gsfc.nasa.gov/pub/data/ace/"

# NOAA URL: FTP path to Kp/Dst indices
# Note: NOAA data is often available via FTP. We use the official NOAA URL.
# If HTTP is required, a mirror might be needed, but we stick to the verified source.
NOAA_URL = "ftp://ftp.ngdc.noaa.gov/STP/space-weather/geomagnetic_indices/kp/"

# Alternative HTTP URLs if FTP is not accessible (for robustness in testing environments)
# These are mirrors or specific file links if available.
# ACE HTTP Mirror (example, may not be official)
# ACE_HTTP_URL = "https://spdf.gsfc.nasa.gov/pub/data/ace/"

# NOAA HTTP Mirror (example)
# NOAA_HTTP_URL = "https://www.ngdc.noaa.gov/stp/space-weather/geomagnetic_indices/kp/"

# We use the FTP URLs as the primary source as per the verified data source requirement.
# If the environment does not support FTP, the fetch functions will fail loudly.

# Output Paths
RAW_DATA_DIR = "data/raw"
PROCESSED_DATA_DIR = "data/processed"
ARTIFACTS_DIR = "artifacts"
FIGURES_DIR = "artifacts/figures"
REPORTS_DIR = "artifacts/reports"
STATE_DIR = "state"

# Correlation Parameters
LAGS_HOURS = [0, 1, 2, 3, 6]
MAX_GAP_HOURS = 6
SIGNIFICANCE_LEVEL = 0.05

# Bonferroni Correction
# Total tests = 3 composition params * 2 geomagnetic indices * 5 lags = 30
TOTAL_TESTS = 30
ALPHA_ADJ = SIGNIFICANCE_LEVEL / TOTAL_TESTS

# File Paths
SYNCED_CSV = "data/processed/synced.csv"
CORRELATION_RESULTS_CSV = "artifacts/correlations.csv"
THRESHOLD_JSON = "artifacts/thresholds/global_threshold.json"
VALIDATION_REPORT_MD = "artifacts/reports/validation_report.md"

# Schema Paths
DATASET_SCHEMA = "contracts/dataset.schema.yaml"
ANALYSIS_SCHEMA = "contracts/analysis_schema.yaml"
THRESHOLD_SCHEMA = "contracts/threshold.schema.yaml"