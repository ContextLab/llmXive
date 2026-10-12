"""
Central configuration constants for the pipeline.
"""

SEED = 42
OUTLIER_SIGMA = 3.0
VIF_THRESHOLD = 10.0
SENSITIVITY_THRESHOLDS = [2.5, 3.0, 3.5]
CONFIDENCE_INTERVAL_TARGET = 0.95
DATA_PATH = "data"
RAW_DATA_PATH = "data/raw"
TARGET_VAR = "conductivity"
