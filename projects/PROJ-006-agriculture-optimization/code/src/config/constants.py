import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Data Paths
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_LOGS = PROJECT_ROOT / "data" / "logs"
DATA_REPORTS = PROJECT_ROOT / "reports"

# Geospatial Constants
BUFFER_SIZE_KM = 1.0  # Buffer size for geospatial fuzzing
GRID_RESOLUTION_KM = 0.1  # Grid resolution for village ID derivation

# Random Seeds
RANDOM_SEED = 42

# Cloud Cover Thresholds
CLOUD_COVER_THRESHOLDS = [0.0, 0.6, 0.7, 0.8, 0.9]

# Statistical Constants
DEFAULT_ALPHA = 0.05
BONFERRONI_TESTS = 3  # Model 1 CSA, Model 2 CSA, Interaction
ADJUSTED_ALPHA = DEFAULT_ALPHA / BONFERRONI_TESTS

# VIF Threshold
VIF_THRESHOLD = 5.0

# Sample Size Thresholds
MIN_SAMPLE_SIZE = 300
MIN_LINKAGE_PERCENTAGE = 95.0
