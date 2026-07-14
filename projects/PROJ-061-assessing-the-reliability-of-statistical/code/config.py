"""
Centralized configuration for the statistical power reliability project.
"""
import os
import json
from typing import Any, Dict, List, Optional
from pathlib import Path

# Project Root
ROOT_DIR = Path(__file__).resolve().parent.parent

# Random Seed
RANDOM_SEED = 42

# Bootstrap Iterations (Configurable)
BOOTSTRAP_ITERATIONS = 1000

# Thresholds for sensitivity analysis (T028)
THRESHOLDS = [0.01, 0.05, 0.10]

# Datasets Configuration (From T004a)
# Selected 10 diverse public datasets: 3 continuous, 3 count, 4 binary
# Source: UCI Machine Learning Repository / OpenML
DATASETS_CONFIG: List[Dict[str, Any]] = [
    # Continuous (3)
    {
        "id": "uci_adult",
        "type": "continuous",
        "source": "uci",
        "dataset_name": "Adult",
        "target_column": "hours-per-week", # Example continuous target
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data"
    },
    {
        "id": "uci_breast_cancer",
        "type": "continuous",
        "source": "uci",
        "dataset_name": "Breast Cancer Wisconsin (Diagnostic)",
        "target_column": "mean radius", # Example continuous feature used as proxy for continuous outcome logic
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/breast-cancer-wisconsin/wdbc.data"
    },
    {
        "id": "uci_concrete",
        "type": "continuous",
        "source": "uci",
        "dataset_name": "Concrete Compressive Strength",
        "target_column": "Concrete compressive strength (MPa)",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/concrete/compressive/Concrete_Compressive_Strength_Data.xlsx" # Note: Real implementation might need CSV conversion or loader adjustment
    },
    # Count (3)
    {
        "id": "openml_biochemical",
        "type": "count",
        "source": "openml",
        "dataset_name": "Biochemical Oxygen Demand",
        "target_column": "bod",
        "url": "https://www.openml.org/api/v1/data/1596"
    },
    {
        "id": "openml_traffic",
        "type": "count",
        "source": "openml",
        "dataset_name": "Traffic Counts",
        "target_column": "count",
        "url": "https://www.openml.org/api/v1/data/42165"
    },
    {
        "id": "uci_fertility",
        "type": "count",
        "source": "uci",
        "dataset_name": "Fertility",
        "target_column": "Number of children", # Hypothetical mapping for demonstration
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/00389/fertility.txt"
    },
    # Binary (4)
    {
        "id": "uci_iris",
        "type": "binary",
        "source": "uci",
        "dataset_name": "Iris",
        "target_column": "class", # Binary classification (e.g., Setosa vs Others)
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data"
    },
    {
        "id": "uci_titanic",
        "type": "binary",
        "source": "uci",
        "dataset_name": "Titanic",
        "target_column": "Survived",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/titanic/titanic3.data"
    },
    {
        "id": "openml_credit",
        "type": "binary",
        "source": "openml",
        "dataset_name": "German Credit",
        "target_column": "creditability",
        "url": "https://www.openml.org/api/v1/data/31"
    },
    {
        "id": "openml_diabetes",
        "type": "binary",
        "source": "openml",
        "dataset_name": "Pima Indians Diabetes",
        "target_column": "Outcome",
        "url": "https://www.openml.org/api/v1/data/1590"
    }
]

def ensure_directories():
    """Create necessary directory structure if it doesn't exist."""
    dirs = [
        "data/raw",
        "data/processed",
        "data/results",
        "code",
        "tests",
        "contracts",
        "figures"
    ]
    for d in dirs:
        path = ROOT_DIR / d
        path.mkdir(parents=True, exist_ok=True)
    return True
