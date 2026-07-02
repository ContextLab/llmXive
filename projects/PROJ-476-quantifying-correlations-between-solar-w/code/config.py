"""
Configuration constants for the Solar Wind - Geomagnetic Correlation Pipeline.

This module defines all critical time boundaries and variable lists used across
the project. All downstream tasks MUST import these constants from `code.config`.

Time Span Documentation:
------------------------
The constants below define the temporal scope of the analysis:
- TRAIN_START (1998) to TEST_END (2020) covers the full 20-year span referenced
  in SC-001 for the "full 20-year lagged correlation analysis" performance benchmark.
- TRAIN_START (1998) to TRAIN_END (2017) defines the subset used for model fitting
  and primary correlation computation.
- TEST_START (2018) to TEST_END (2020) defines the held-out validation period
  used for independent verification of correlation stability (US3).
"""

# Time boundaries for analysis
# Full span: 1998-2020 (20 years) as per SC-001
TRAIN_START = 1998
TRAIN_END = 2017
TEST_START = 2018
TEST_END = 2020

# ACE (Advanced Composition Explorer) Solar Wind Variables
# Source: ACE Level 2 SWEPAM/SWICS data
# Required column names in raw data must match these exactly for validation
ACE_VARS = ['N_p', 'T_p', 'He2+_ratio']

# NOAA Geomagnetic Indices
# Source: NOAA NGDC Kp and Dst indices
NOAA_VARS = ['Kp', 'Dst']

# Derived: Total number of tests for Bonferroni correction
# 3 ACE vars * 2 NOAA indices * 5 lags = 30 tests
# Used in T023 for dynamic calculation of alpha_adj
TOTAL_TESTS = len(ACE_VARS) * len(NOAA_VARS) * 5