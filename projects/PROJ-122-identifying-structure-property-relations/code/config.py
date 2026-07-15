"""
Configuration settings for the polymer blend structure-property pipeline.
"""
import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent

# Data Paths
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_FEATURES_DIR = PROJECT_ROOT / "data" / "features"
DATA_OUTPUT_DIR = PROJECT_ROOT / "data" / "output"

# State Paths
STATE_DIR = PROJECT_ROOT / "state"
PROJECT_STATE_FILE = STATE_DIR / "projects" / "PROJ-122-identifying-structure-property-relations.yaml"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = PROJECT_ROOT / "logs"

# Random Seed
RANDOM_SEED = 42

# Weight Fraction Validation
# Configurable list of tolerance thresholds for sensitivity analysis (FR-014)
# Default range covers strict to lenient validation
WEIGHT_FRACTION_TOLERANCES = [0.001, 0.01, 0.02, 0.05, 0.1]

# Data Quality Thresholds
MIN_VALID_RECORDS_THRESHOLD = 100
MAX_MISSING_VALUE_RATIO = 0.2

# Execution Limits
MAX_RAM_CAPACITY_GB = 14.0  # Default fallback if not detected
MAX_DATASET_ROWS = 100000  # Safety limit for streaming

# Feature Engineering
DESCRIPTOR_COUNT_MIN = 15
VIF_THRESHOLD = 5.0
VIF_CRITICAL_THRESHOLD = 10.0

# Model Training
TRAIN_TEST_SPLIT_RATIO = 0.8
CV_FOLDS = 5
MIN_DATASET_SIZE = 100

# Statistical Testing
PAIRED_TTEST_CORRECTION_METHOD = "bonferroni"  # Options: 'bonferroni', 'fdr'

# Fallback Triggers
PERFECT_JOIN_FAILURE_RATE_THRESHOLD = 0.5  # 50%

# Paths for reports
TOLERANCE_SENSITIVITY_REPORT_PATH = DATA_OUTPUT_DIR / "tolerance_sensitivity_report.json"
DATA_QUALITY_REPORT_PATH = DATA_OUTPUT_DIR / "data_quality_report.json"
VIF_REPORT_PATH = DATA_FEATURES_DIR / "vif_report.json"
BASELINE_METRICS_PATH = DATA_FEATURES_DIR / "baseline_metrics.json"
STABILITY_METRICS_PATH = DATA_FEATURES_DIR / "stability_metrics.json"
