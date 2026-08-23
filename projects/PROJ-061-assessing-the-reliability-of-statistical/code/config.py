import os
import json
from typing import Any, Dict, List, Optional
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Random Seed
RANDOM_SEED = 42

# Bootstrap Iterations
BOOTSTRAP_ITERATIONS = 1000

# Dataset Configuration (Populated by T004a)
DATASET_LIST = [
    {"id": "iris", "source": "uci", "type": "continuous", "url": "https://archive.ics.uci.edu/ml/datasets/iris"},
    {"id": "wine", "source": "uci", "type": "continuous", "url": "https://archive.ics.uci.edu/ml/datasets/wine"},
    {"id": "breast_cancer", "source": "uci", "type": "binary", "url": "https://archive.ics.uci.edu/ml/datasets/breast+cancer+wisconsin+(diagnostic)"},
    {"id": "heart_disease", "source": "uci", "type": "binary", "url": "https://archive.ics.uci.edu/ml/datasets/heart+disease"},
    {"id": "diabetes", "source": "uci", "type": "binary", "url": "https://archive.ics.uci.edu/ml/datasets/diabetes"},
    {"id": "boston_housing", "source": "uci", "type": "continuous", "url": "https://archive.ics.uci.edu/ml/datasets/housing"},
    {"id": "concrete", "source": "uci", "type": "continuous", "url": "https://archive.ics.uci.edu/ml/datasets/Concrete+Compressive+Strength"},
    {"id": "yacht", "source": "uci", "type": "continuous", "url": "https://archive.ics.uci.edu/ml/datasets/yacht+hydrodynamics"},
    {"id": "bank", "source": "uci", "type": "binary", "url": "https://archive.ics.uci.edu/ml/datasets/bank+marketing"},
    {"id": "credit_giving", "source": "uci", "type": "binary", "url": "https://archive.ics.uci.edu/ml/datasets/statlog+(german+credit+data)"}
]

# Violation Sweep Configuration (T021b)
VIOLATION_SWEEP_CONFIG = {
    "heavy_tailed": {
        "param_name": "df",
        "values": [3.0, 5.0, 10.0, 30.0],  # Degrees of freedom (lower = heavier tails)
        "description": "Degrees of freedom for t-distribution noise injection"
    },
    "ar1_autocorrelation": {
        "param_name": "rho",
        "values": [0.2, 0.4, 0.6, 0.8],
        "description": "AR(1) coefficient for autocorrelation injection"
    },
    "effect_size_heterogeneity": {
        "param_name": "mixing_ratio",
        "values": [0.1, 0.2, 0.3, 0.4],
        "description": "Mixing ratio for sub-population injection (T021 spec: 0.2 default, 1.5 SD separation)"
    }
}

# Thresholds for Sensitivity Analysis (US3)
THRESHOLDS = [0.01, 0.05, 0.10]

def ensure_directories():
    """Create required directory structure if it doesn't exist."""
    dirs = [
        PROJECT_ROOT / "data" / "raw",
        PROJECT_ROOT / "data" / "processed",
        PROJECT_ROOT / "data" / "results",
        PROJECT_ROOT / "code",
        PROJECT_ROOT / "tests"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    # Ensure __init__.py files exist
    for d in [PROJECT_ROOT / "code", PROJECT_ROOT / "tests"]:
        (d / "__init__.py").touch()

if __name__ == "__main__":
    ensure_directories()
    print("Directories ensured.")
