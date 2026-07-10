"""
Model configuration and constants.

This module contains configuration parameters and constants for the
molecular toxicity prediction models.
"""
from typing import Dict, Any

# Default model parameters
DEFAULT_MODEL_CONFIG: Dict[str, Any] = {
    "rule_based": {
        "config_path": "config/structural_alerts.json",
        "threshold": 0.0
    },
    "logistic_regression": {
        "n_splits": 5,
        "n_repeats": 3,
        "random_state": 42,
        "C": 1.0,
        "max_iter": 1000
    }
}

# Feature importance thresholds
FEATURE_IMPORTANCE_THRESHOLD: float = 0.01

# Model evaluation metrics
EVALUATION_METRICS: list = [
    "roc_auc",
    "f1",
    "recall",
    "precision"
]

# Cross-validation strategy
CV_STRATEGY: Dict[str, Any] = {
    "type": "stratified",
    "n_splits": 5,
    "n_repeats": 3,
    "shuffle": True
}

# Memory limits (in bytes)
MEMORY_LIMIT: int = 7 * 1024 * 1024 * 1024  # 7 GB

# Performance targets
TARGET_EXECUTION_TIME_HOURS: float = 4.0

# Dataset requirements
MIN_DATASET_SIZE: int = 1000

# Statistical significance threshold
SIGNIFICANCE_THRESHOLD: float = 0.05
