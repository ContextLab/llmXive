import os
import json
from typing import Any, Dict, List, Optional
from pathlib import Path

# Random seed for reproducibility
RANDOM_SEED = 42

# Bootstrap iterations for empirical power estimation
BOOTSTRAP_ITERATIONS = 1000

# Dataset configuration (populated by T004a)
DATASETS_CONFIG = [
    {
        "id": "iris",
        "name": "Iris",
        "source": "uci",
        "type": "continuous",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data"
    },
    {
        "id": "mtcars",
        "name": "Motor Trend Car Road Tests",
        "source": "uci",
        "type": "continuous",
        "url": "https://raw.githubusercontent.com/vincentarelbundock/Rdatasets/master/csv/datasets/mtcars.csv"
    },
    {
        "id": "concrete",
        "name": "Concrete Compressive Strength",
        "source": "uci",
        "type": "continuous",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/concrete/compressive/Concrete_Compressive_Strength_Data.csv"
    },
    {
        "id": "poisson_data",
        "name": "Poisson Count Data Example",
        "source": "synthetic_ref",
        "type": "count",
        "url": "https://raw.githubusercontent.com/plotly/datasets/master/poisson_example.csv"
    },
    {
        "id": "count_1",
        "name": "Count Data Set 1",
        "source": "openml",
        "type": "count",
        "url": "https://www.openml.org/api/v1/data/2929"
    },
    {
        "id": "count_2",
        "name": "Count Data Set 2",
        "source": "openml",
        "type": "count",
        "url": "https://www.openml.org/api/v1/data/2930"
    },
    {
        "id": "binary_1",
        "name": "Binary Classification 1",
        "source": "openml",
        "type": "binary",
        "url": "https://www.openml.org/api/v1/data/554"
    },
    {
        "id": "binary_2",
        "name": "Binary Classification 2",
        "source": "openml",
        "type": "binary",
        "url": "https://www.openml.org/api/v1/data/556"
    },
    {
        "id": "binary_3",
        "name": "Binary Classification 3",
        "source": "openml",
        "type": "binary",
        "url": "https://www.openml.org/api/v1/data/557"
    },
    {
        "id": "binary_4",
        "name": "Binary Classification 4",
        "source": "openml",
        "type": "binary",
        "url": "https://www.openml.org/api/v1/data/559"
    }
]

# Violation sweep configuration for T021b (SC-001)
# Defines the ranges for parameter sweeps to generate bias curves
VIOLATION_SWEEP_CONFIG = {
    "heavy_tailed": {
        "parameter": "df",
        "description": "Degrees of freedom for t-distribution (lower = heavier tails)",
        "values": [1.0, 2.0, 3.0, 5.0, 10.0, 30.0],  # 30 approximates normal
        "default": 30.0
    },
    "ar1_autocorrelation": {
        "parameter": "rho",
        "description": "AR(1) coefficient (0 = no autocorrelation, 1 = perfect)",
        "values": [0.0, 0.2, 0.4, 0.6, 0.8],
        "default": 0.0
    },
    "effect_size_heterogeneity": {
        "parameter": "mixing_ratio",
        "description": "Proportion of the secondary sub-population",
        "values": [0.0, 0.1, 0.2, 0.3, 0.4],
        "default": 0.0,
        # Fixed parameters for this sweep as per T021 spec
        "fixed_separation": 1.5,  # standard deviations
        "fixed_ratio": 0.2        # default mixing ratio if not swept
    }
}

# Sensitivity analysis thresholds (T028)
THRESHOLDS = [0.01, 0.05, 0.10]

def ensure_directories():
    """Create necessary project directories if they don't exist."""
    dirs = [
        "code",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "data/raw",
        "data/processed",
        "data/results",
        "docs"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

    # Create __init__.py files
    init_files = [
        "code/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py",
        "tests/contract/__init__.py"
    ]
    for f in init_files:
        Path(f).touch()

if __name__ == "__main__":
    ensure_directories()
    print("Directories ensured.")
