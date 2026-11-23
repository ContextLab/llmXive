import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_PATH = PROJECT_ROOT / "data"
LOG_PATH = PROJECT_ROOT / "data" / "logs"

# Classifier configuration
CLASSIFIER_THRESHOLD = 0.8
CLASSIFIER_MODEL_PATH = PROJECT_ROOT / "models" / "codebert_onnx"

# GitHub API configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_API_RATE_LIMIT = 5000

# Matching configuration
MATCHING_RATIO = 1.0
MATCHING_METHOD = "nearest_neighbor"

# Statistical analysis configuration
SIGNIFICANCE_LEVEL = 0.05
EFFECT_SIZE_THRESHOLD = 0.5
POWER_THRESHOLD = 0.80

# File paths for outputs
MANUAL_LABELS_PATH = DATA_PATH / "ground_truth" / "manual_labels.csv"
CLASSIFIER_METRICS_PATH = DATA_PATH / "ground_truth" / "classifier_metrics.json"
MATCHED_PAIRS_PATH = DATA_PATH / "processed" / "matched_pairs_filtered.csv"
METRICS_LONGITUDINAL_PATH = DATA_PATH / "processed" / "metrics_longitudinal.csv"
