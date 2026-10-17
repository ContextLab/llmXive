"""
Configuration constants for the Solar Wind Composition and Geomagnetic Indices project.

This module defines all project-wide constants including date ranges, variable names,
and verified data source URLs. All downstream tasks MUST import these constants from
this module.

IMPORTANT: TRAIN_START (1998) to TEST_END (2020) covers the full multi-decadal span
referenced in SC-001 for the "full 20-year lagged correlation analysis" performance
benchmark, while TRAIN_START (1998) to TRAIN_END (2017) is the subset used for model
fitting.
"""

# Date Ranges
# TRAIN_START to TEST_END covers the full multi-decadal span referenced in SC-001
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

# Memory limits (used by the fetch and streaming utilities)
MAX_MEMORY_GB = 7  # SC-001: full-run analysis must stay within 7 GB RAM

# Verified Data Source URLs
# These URLs are the single source of truth for data acquisition.
# If these URLs are unreachable, the pipeline MUST fail loudly.
# ACE URL: FTP path to Level 2 data (SWEPAM/SWICS)
ACE_URL = "ftp://spdf.gsfc.nasa.gov/pub/data/ace/"

# NOAA URL: FTP path to Kp/Dst indices
NOAA_URL = "ftp://ftp.ngdc.noaa.gov/STP/space-weather/geomagnetic_indices/kp/"

# Specific sub-paths used by the fetch module.
ACE_SWEPAM_URL = ACE_URL + "swepam/level2/"
ACE_SWICS_URL = ACE_URL + "swics/level2/"
NOAA_KP_DST_URL = NOAA_URL  # NOAA Kp/Dst data resides under this FTP path.

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

# Streaming / chunk size for large-file processing
# Used by alignment and Neff calculation utilities.
STREAMING_CHUNK_SIZE = 100_000
