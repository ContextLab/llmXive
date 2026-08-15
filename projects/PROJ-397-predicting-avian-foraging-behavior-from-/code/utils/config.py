"""
Configuration module for the avian foraging behavior prediction pipeline.
Defines paths, random seeds, and constants used across the project.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import numpy as np
import random

# Project root is the parent of the 'code' directory
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Default random seed for reproducibility
_DEFAULT_SEED = 42
_CURRENT_SEED = _DEFAULT_SEED

# Constants
BUFFER_RADIUS_METERS = 100
MIN_OBSERVATIONS_PER_SPECIES = 50
TOP_N_SPECIES = 25
PERMUTATION_ITERATIONS = 1000
RANDOM_STATE = 42

# NLCD 2019 Land Cover Classes (standard USGS mapping)
NLCD_CLASSES = {
    11: "open_water",
    12: "perennial_ice_snow",
    21: "developed_open_space",
    22: "developed_low_intensity",
    23: "developed_medium_intensity",
    24: "developed_high_intensity",
    31: "barren_land",
    41: "deciduous_forest",
    42: "evergreen_forest",
    43: "mixed_forest",
    51: "dwarf_scrub",
    52: "shrub_scrub",
    71: "grassland_herbaceous",
    72: "sedge_herbaceous",
    73: "loses",
    74: "savannas",
    81: "palustrine_emergent_persistent",
    82: "palustrine_forested",
    83: "palustrine_scrub_shrub",
    90: "woody_wetlands",
    95: "estuarine_marine_emergent_persistent",
}

# Land cover categories for aggregation (grouping detailed classes)
LAND_COVER_GROUPS = {
    "forest": [41, 42, 43],
    "grassland": [71, 72, 73, 74],
    "wetland": [81, 82, 83, 90, 95],
    "urban": [21, 22, 23, 24],
    "water": [11, 12],
    "barren": [31, 51],
    "shrub": [52],
}

def get_project_root() -> Path:
    """Return the project root directory."""
    return _PROJECT_ROOT

def get_data_dir() -> Path:
    """Return the data directory."""
    return get_project_root() / "data"

def get_raw_data_dir() -> Path:
    """Return the raw data directory."""
    data_dir = get_data_dir()
    raw_dir = data_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    return raw_dir

def get_processed_dir() -> Path:
    """Return the processed data directory."""
    data_dir = get_data_dir()
    processed_dir = data_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    return processed_dir

def get_models_dir() -> Path:
    """Return the models directory."""
    models_dir = get_project_root() / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    return models_dir

def get_viz_dir() -> Path:
    """Return the visualization directory."""
    viz_dir = get_project_root() / "viz"
    viz_dir.mkdir(parents=True, exist_ok=True)
    return viz_dir

def get_figures_dir() -> Path:
    """Return the figures directory."""
    viz_dir = get_viz_dir()
    figures_dir = viz_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    return figures_dir

def get_reports_dir() -> Path:
    """Return the reports directory."""
    reports_dir = get_project_root() / "docs" / "results"
    reports_dir.mkdir(parents=True, exist_ok=True)
    return reports_dir

def ensure_directories():
    """Ensure all required directories exist."""
    get_data_dir()
    get_raw_data_dir()
    get_processed_dir()
    get_models_dir()
    get_viz_dir()
    get_figures_dir()
    get_reports_dir()

def get_seed() -> int:
    """Return the current random seed."""
    return _CURRENT_SEED

def set_seed(seed: int):
    """Set the random seed for reproducibility."""
    global _CURRENT_SEED
    _CURRENT_SEED = seed
    random.seed(seed)
    np.random.seed(seed)

def get_model_params() -> Dict[str, Any]:
    """Return default Random Forest model parameters."""
    return {
        "n_estimators": 100,
        "max_depth": None,
        "min_samples_split": 2,
        "min_samples_leaf": 1,
        "random_state": get_seed(),
        "n_jobs": -1,
    }

def get_cv_params() -> Dict[str, Any]:
    """Return default cross-validation parameters."""
    return {
        "n_splits": 5,
        "shuffle": True,
        "random_state": get_seed(),
    }

def get_permutation_params() -> Dict[str, Any]:
    """Return default permutation test parameters."""
    return {
        "n_iterations": PERMUTATION_ITERATIONS,
        "random_state": get_seed(),
    }

def get_data_thresholds() -> Dict[str, Any]:
    """Return data processing thresholds."""
    return {
        "min_observations": MIN_OBSERVATIONS_PER_SPECIES,
        "top_n_species": TOP_N_SPECIES,
    }

def get_file_paths() -> Dict[str, Path]:
    """Return all key file paths."""
    return {
        "metadata": get_data_dir() / "metadata.yaml",
        "ebd_raw": get_raw_data_dir() / "ebd_train.csv",
        "nlcd_raw": get_raw_data_dir() / "nlcd_2019.zip",
        "guild_source": get_raw_data_dir() / "guild_source.csv",
        "guild_mapping": get_processed_dir() / "guild_mapping.csv",
        "top_species_ids": get_processed_dir() / "top_25_species_ids.json",
        "merged_observations": get_processed_dir() / "merged_observations.csv",
        "species_profiles": get_processed_dir() / "species_profiles.csv",
        "top_species_viz": get_processed_dir() / "top_25_species_for_viz.json",
        "model": get_models_dir() / "random_forest.pkl",
        "evaluation_metrics": get_reports_dir() / "evaluation_metrics.json",
        "confusion_matrix": get_figures_dir() / "confusion_matrix.png",
        "importance_chart": get_figures_dir() / "feature_importance.png",
        "habitat_map": get_figures_dir() / "habitat_map.png",
        "importance_report": get_reports_dir() / "feature_importance_report.md",
    }

# Initialize directories on import
ensure_directories()
set_seed(_DEFAULT_SEED)