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
    },
    "random_seed": 42,
    "thresholds": [0.1, 0.2, 0.3, 0.4, 0.5],
    "default_threshold": 0.3,
    "n_permutations": 1000,
    "n_permutations_large_clustering": 500,
    "min_continuous_vars": 20,
    "max_line_length": 88,
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
