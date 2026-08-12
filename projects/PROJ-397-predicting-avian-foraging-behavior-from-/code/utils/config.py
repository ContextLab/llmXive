"""
Configuration module for the Avian Foraging Behavior prediction pipeline.
Defines paths, random seeds, and constants used across the project.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import numpy as np
import random

# --- Constants ---
RANDOM_SEED: int = 42
N_FOLDS: int = 5
MAX_OBSERVATIONS_PER_SPECIES: int = 10000
MIN_OBSERVATIONS_PER_SPECIES: int = 50
BUFFER_RADIUS_M: int = 100
LAND_COVER_CLASSES: List[str] = [
    "OPEN_WATER",
    "PERENNIAL_SNOW_ICE",
    "DEVELOPED_OPEN_SPACE",
    "DEVELOVED_LOW_INTENSITY",
    "DEVELOPED_MEDIUM_INTENSITY",
    "DEVELOPED_HIGH_INTENSITY",
    "BARREN_LAND",
    "DECIDUOUS_FOREST",
    "EVERGREEN_FOREST",
    "MIXED_FOREST",
    "DENSE_SHRUB_SCRUB",
    "SHRUB_SCRUB",
    "GRASSLAND_HERBACEOUS",
    "SAGEBRUSH_SCRUB",
    "WOODY_WETLANDS",
    "EMERGENT_HERBACEOUS_WETLANDS",
    "CROPLAND",
    "PASTURE_HAY",
]

# --- Project Root Detection ---
# Assumes the project root is the parent of the 'code' directory
# If run directly from 'code', it adjusts accordingly.
def get_project_root() -> Path:
    """Returns the absolute path to the project root directory."""
    current_file = Path(__file__).resolve()
    # If this file is in code/utils/config.py, root is 3 levels up
    # If the script is run from the repo root, this logic holds if 'code' exists.
    # Fallback: check if 'code' is a subdirectory of the current working dir parent.
    root = current_file.parent.parent.parent
    if not root.joinpath("data").exists():
        # Fallback logic if structure is different (e.g. running from code/)
        root = current_file.parent.parent
        if not root.joinpath("data").exists():
            # Final fallback to cwd if structure is unexpected, though spec implies fixed structure
            root = Path.cwd()
    return root

# --- Directory Paths ---
def get_data_dir() -> Path:
    """Returns the path to the data directory."""
    return get_project_root() / "data"

def get_raw_data_dir() -> Path:
    """Returns the path to the raw data directory."""
    return get_data_dir() / "raw"

def get_processed_dir() -> Path:
    """Returns the path to the processed data directory."""
    return get_data_dir() / "processed"

def get_models_dir() -> Path:
    """Returns the path to the models directory."""
    return get_data_dir() / "models"

def get_viz_dir() -> Path:
    """Returns the path to the visualization directory."""
    return get_data_dir() / "viz"

def get_figures_dir() -> Path:
    """Returns the path to the figures directory."""
    return get_viz_dir() / "figures"

def get_reports_dir() -> Path:
    """Returns the path to the reports directory."""
    return get_data_dir() / "reports"

# --- Hyperparameters & Configs ---
def get_seed() -> int:
    """Returns the global random seed."""
    return RANDOM_SEED

def set_seed(seed: int = RANDOM_SEED) -> None:
    """Sets the random seed for reproducibility across numpy, random, and torch (if available)."""
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

def get_model_params() -> Dict[str, Any]:
    """Returns default parameters for the Random Forest model."""
    return {
        "n_estimators": 100,
        "max_depth": None,
        "min_samples_split": 2,
        "min_samples_leaf": 1,
        "random_state": get_seed(),
        "n_jobs": -1,
    }

def get_cv_params() -> Dict[str, Any]:
    """Returns default parameters for K-Fold Cross Validation."""
    return {
        "n_splits": N_FOLDS,
        "shuffle": True,
        "random_state": get_seed(),
    }

def get_permutation_params() -> Dict[str, Any]:
    """Returns parameters for the stratified permutation test."""
    return {
        "n_permutations": 1000,
        "random_state": get_seed(),
        "stratify_by": "species_id",
    }

def get_data_thresholds() -> Dict[str, int]:
    """Returns data filtering thresholds."""
    return {
        "min_observations": MIN_OBSERVATIONS_PER_SPECIES,
        "max_observations": MAX_OBSERVATIONS_PER_SPECIES,
        "buffer_radius_m": BUFFER_RADIUS_M,
    }

# --- File Paths ---
def get_file_paths() -> Dict[str, Path]:
    """Returns a dictionary of key file paths used in the pipeline."""
    return {
        "guild_mapping": get_processed_dir() / "guild_mapping.csv",
        "top_species_ids": get_processed_dir() / "top_species_ids.json",
        "ebd_filtered": get_processed_dir() / "ebd_filtered.csv",
        "merged_observations": get_processed_dir() / "merged_observations.csv",
        "species_profiles": get_processed_dir() / "species_profiles.csv",
        "top_species": get_processed_dir() / "top_species.json",
        "model_path": get_models_dir() / "random_forest.pkl",
        "evaluation_metrics": get_processed_dir() / "evaluation_metrics.json",
        "confusion_matrix_fig": get_figures_dir() / "confusion_matrix.png",
        "importance_fig": get_figures_dir() / "feature_importance.png",
        "habitat_map_fig": get_figures_dir() / "habitat_map.png",
        "habitat_map_geojson": get_figures_dir() / "habitat_map.geojson",
        "feature_importance_report": get_reports_dir() / "feature_importance_report.md",
    }

def ensure_directories() -> None:
    """Creates all required directories if they do not exist."""
    dirs = [
        get_raw_data_dir(),
        get_processed_dir(),
        get_models_dir(),
        get_viz_dir(),
        get_figures_dir(),
        get_reports_dir(),
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)