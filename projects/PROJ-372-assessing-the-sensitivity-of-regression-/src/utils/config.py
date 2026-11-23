"""
Configuration management for the sensitivity analysis pipeline.
Loads research parameters (like sample size tiers) from the specification.
"""
import os
from typing import List, Dict, Any
from pathlib import Path

# Default configuration values if not overridden by environment or file
_DEFAULT_CONFIG = {
    "sample_size_tiers": [10, 25, 50, 75, 90],
    "num_subsets_per_tier": 200,
    "convergence_threshold_pct": 5.0,
    "violation_thresholds": {
        "low_pval": 0.10,
        "medium_pval": 0.05,
    },
    "random_seed": 42,
    "max_rows_to_profile": 100_000,
    "memory_limit_bytes": 7 * 1024 * 1024 * 1024,  # 7GB
}

def get_sample_size_tiers() -> List[int]:
    """
    Returns the list of sample size tier percentages to use for resampling.
    These values are sourced from the specification (spec.md) to ensure
    consistency with the research design.
    
    Returns:
        List[int]: A list of integers representing percentage values (e.g., [10, 25, ...]).
    """
    # In a real deployment, this could read from a YAML/JSON config file
    # or environment variables. For now, it returns the spec-defined defaults.
    return _DEFAULT_CONFIG["sample_size_tiers"]

def get_num_subsets_per_tier() -> int:
    """Returns the number of subsets to generate per tier."""
    return _DEFAULT_CONFIG["num_subsets_per_tier"]

def get_convergence_threshold() -> float:
    """Returns the threshold for convergence (Standard Error of SD)."""
    return _DEFAULT_CONFIG["convergence_threshold_pct"]

def get_random_seed() -> int:
    """Returns the global random seed."""
    return _DEFAULT_CONFIG["random_seed"]

def get_violation_thresholds() -> Dict[str, float]:
    """Returns thresholds for classifying violation severity."""
    return _DEFAULT_CONFIG["violation_thresholds"]

def get_project_root() -> Path:
    """Returns the root path of the project."""
    return Path(__file__).resolve().parent.parent.parent

def get_data_dir() -> Path:
    """Returns the path to the data directory."""
    return get_project_root() / "data"

def get_artifacts_dir() -> Path:
    """Returns the path to the artifacts directory."""
    return get_project_root() / "artifacts"

def get_specs_dir() -> Path:
    """Returns the path to the specs directory."""
    return get_project_root() / "specs" / "001-sensitivity-regression-coefficients"
