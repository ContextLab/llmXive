"""Configuration module for the statistical significance analysis pipeline.

Defines paths, random seeds, default thresholds, and utility functions for
directory management.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Root directory relative to this file
_ROOT_DIR = Path(__file__).parent.parent

# Configuration keys
CONFIG: Dict[str, Any] = {
    "paths": {
        "data_raw": "data/raw",
        "data_processed": "data/processed",
        "output_results": "output/results",
        "output_plots": "output/plots",
        "output_plots_primary": "output/plots/primary",
        "output_reports": "output/reports",
        "output_exploratory": "output/exploratory",
        "output_logs": "output/logs",
    },
    "random_seed": 42,
    "thresholds": [0.1, 0.2, 0.3, 0.4, 0.5],
    "default_threshold": 0.3,
    "n_permutations": 1000,
    "n_permutations_large_clustering": 500,
    "min_continuous_vars": 20,
    "max_line_length": 88,
    "datasets": {
        "wine": {
            "name": "Wine",
            "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/wine/wine.data",
            "header": None,
            "sep": ",",
        },
        "abalone": {
            "name": "Abalone",
            "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/abalone/abalone.data",
            "header": None,
            "sep": ",",
        },
        "breast_cancer": {
            "name": "Breast Cancer Wisconsin",
            "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/breast-cancer-wisconsin/breast-cancer-wisconsin.data",
            "header": None,
            "sep": ",",
        },
        "student_performance": {
            "name": "Student Performance",
            "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/00256/student-mat.csv",
            "header": 0,
            "sep": ";",
        },
        "air_quality": {
            "name": "Air Quality",
            "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/00360/AirQualityUCI.csv",
            "header": 0,
            "sep": ";",
            "encoding": "cp1252",
            "note": "Direct CSV link from UCI repository to avoid ZIP extraction complexity."
        },
        "concrete": {
            "name": "Concrete Compressive Strength",
            "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/concrete/compressive/Concrete_Data.xls",
            "header": 0,
            "ext": "xls",
        },
    },
    "fallback_datasets": {
        "parkinsons": {
            "name": "Parkinsons",
            "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/parkinsons/parkinsons.data",
            "header": None,
            "sep": ",",
        },
        "libras": {
            "name": "Libras",
            "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/00242/Libras_movement.data",
            "header": None,
            "sep": ",",
        },
        "isolet": {
            "name": "Isolet",
            "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/isolet/isolet_train_data",
            "header": None,
            "sep": " ",
        },
    },
}


def get_config() -> Dict[str, Any]:
    """Return the full configuration dictionary.

    Returns:
        Dict[str, Any]: The configuration dictionary containing paths and parameters.
    """
    return CONFIG.copy()


def ensure_dirs() -> None:
    """Ensure all required directories exist.

    Creates directories defined in CONFIG['paths'] relative to the project root.
    """
    paths = CONFIG["paths"]
    for dir_name in paths.values():
        dir_path = _ROOT_DIR / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
