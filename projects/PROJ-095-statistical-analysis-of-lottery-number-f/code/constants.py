"""
Lottery draw parameters and constants.

This module defines the core configuration for the lottery analysis pipeline,
ensuring consistency across all metrics and validation logic.
"""

# Draw Configuration
NUMBERS_PER_DRAW = 6
MAX_BALL = 49
MIN_BALL = 1

# Analysis Thresholds
BIRTHDAY_THRESHOLD = 31  # Numbers <= 31 correspond to valid calendar days
BIRTHDAY_CLUSTER_RATIO_THRESHOLD = 0.5  # Threshold for flagging majority birthday draws

# Sales and Jackpot Parameters
INSUFFICIENT_DATA_COUNT_THRESHOLD = 5  # Minimum draws required per tier for analysis
OUTLIER_MULTIPLIER = 10.0  # Multiplier for global mean to define extreme outliers

# Statistical Parameters
DEFAULT_CONFIDENCE_LEVEL = 0.95
BOOTSTRAP_ITERATIONS = 1000
BONFERRONI_TESTS = 2  # Number of simultaneous hypothesis tests (birthday + consecutive)

# Data Validation
MISSING_SALES_WARNING_THRESHOLD = 0.2  # Fraction of missing sales data to trigger warning
CI_WIDTH_PRECISION_FACTOR = 0.2  # CI width relative to effect size for precision check

# File Paths (Relative to project root)
RAW_DATA_DIR = "data/raw"
PROCESSED_DATA_DIR = "data/processed"
RESULTS_DIR = "data/results"
CONFIG_DIR = "config"
SCHEMAS_DIR = "data/schemas"

# Specific File Names
RAW_CSV_FILENAME = "lottery_draws.csv"
METRICS_JSON_FILENAME = "metrics.json"
CORRELATION_RESULT_FILENAME = "correlation_result.json"
VALIDATION_REPORT_FILENAME = "validation_report.json"
HYPOTHESIS_TESTS_FILENAME = "hypothesis_tests.json"
FINAL_REPORT_FILENAME = "final_report.json"
DATA_SOURCES_CONFIG = "data_sources.json"
CHECKSUMS_FILENAME = "checksums.json"
LEGACY_METRICS_FILENAME = "legacy_metrics.json"
FINAL_REPORT_SCHEMA = "final_report.schema.json"

# Control Variable Note (Mandated by FR-004)
CONTROL_VARIABLE_NOTE = "Quick Pick rate unobservable; no control applied"