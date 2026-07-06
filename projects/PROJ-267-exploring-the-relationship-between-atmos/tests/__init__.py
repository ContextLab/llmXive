"""
Test suite for the Atmospheric River Gravity Correlation project.

This package contains contract tests, integration tests, and unit tests
for validating the data pipeline, statistical analysis, and visualization outputs.
"""

# Test configuration and fixtures can be added here as needed
__version__ = "0.1.0"

# Common test constants
PROJECT_ROOT = "projects/PROJ-267-exploring-the-relationship-between-atmos"
DATA_DIR = f"{PROJECT_ROOT}/data"
CODE_DIR = f"{PROJECT_ROOT}/code"
OUTPUT_DIR = f"{PROJECT_ROOT}/output"

# Test timeouts (in seconds)
PIPELINE_TIMEOUT = 3600  # 1 hour for long-running pipelines
UNIT_TEST_TIMEOUT = 30   # 30 seconds for individual unit tests

# Expected file paths for validation
EXPECTED_MERGED_DATA = f"{DATA_DIR}/processed/merged_monthly.csv"
EXPECTED_CORRELATION_OUTPUT = f"{OUTPUT_DIR}/correlation_results.json"
EXPECTED_TIMESERIES_PLOT = f"{OUTPUT_DIR}/timeseries_overlay.png"
EXPECTED_SCATTER_PLOT = f"{OUTPUT_DIR}/scatter_regression.png"
EXPECTED_SPATIAL_MAP = f"{OUTPUT_DIR}/spatial_anomaly_map.png"

# Schema validation paths
DATASET_SCHEMA = f"{PROJECT_ROOT}/contracts/dataset.schema.yaml"
OUTPUT_SCHEMA = f"{PROJECT_ROOT}/contracts/output.schema.yaml"