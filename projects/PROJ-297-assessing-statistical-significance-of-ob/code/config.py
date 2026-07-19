"""
Configuration module for the pipeline.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional

def get_config() -> Dict[str, Any]:
    """Return configuration dictionary."""
    return {
        "random_seed": 42,
        "min_datasets": 3,
        "default_permutations": 1000,
        "default_threshold": 0.3,
        "max_memory_gb": 5.6,
        "n_min": 500,
        "time_limit_seconds": 21600
    }

def ensure_dirs():
    """Ensure required directories exist."""
    dirs = [
        "data/raw",
        "data/processed",
        "output/results",
        "output/plots",
        "output/reports",
        "output/exploratory",
        "state"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

# Dataset URLs (T004)
DATASETS = [
    {"id": "wine", "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/wine/wine.data"},
    {"id": "abalone", "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/abalone/abalone.data"},
    {"id": "breast_cancer", "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/breast-cancer-wisconsin/wdbc.data"},
    {"id": "student_performance", "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/00295/student-mat.csv"},
    {"id": "air_quality", "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/00360/AirQualityUCI.zip"},
    {"id": "concrete", "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/concrete/compressive/concrete_compressive_strength.xls"}
]

FALLBACK_DATASETS = [
    {"id": "parkinsons", "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/parkinsons/parkinsons.data"},
    {"id": "libras", "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/libras/movement-libras.data"},
    {"id": "isolet", "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/isolet/isolet1_train_data"}
]

def main():
    pass

if __name__ == "__main__":
    ensure_dirs()
