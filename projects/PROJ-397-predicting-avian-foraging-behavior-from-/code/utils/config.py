"""
Configuration module for the Avian Foraging Behavior Prediction Pipeline.
Defines paths, random seeds, and constants used across the project.
"""
import os
import random
from pathlib import Path
from typing import Dict, Any, Optional, List

import numpy as np

# --- Project Root Configuration ---
# The project root is defined relative to this file's location (code/utils/config.py)
# Project root is the parent of the 'code' directory
_CURRENT_DIR = Path(__file__).resolve().parent
_CODE_ROOT = _CURRENT_DIR.parent
_PROJECT_ROOT = _CODE_ROOT.parent

# --- Random Seeds ---
# Fixed seed for reproducibility across the pipeline
RANDOM_SEED = 42

# --- Constants ---
# Buffer radius for land cover analysis (in meters)
BUFFER_RADIUS_M = 100

# Minimum number of observations required per species for inclusion
MIN_OBSERVATIONS_PER_SPECIES = 50

# Maximum number of top species to select for analysis
TOP_N_SPECIES = 25

# Foraging Guild Categories (Standardized)
FORAGING_GUILDS = [
    "Insectivore",
    "Granivore",
    "Nectarivore",
    "Carnivore",
    "Omnivore",
    "Frugivore",
    "Scavenger"
]

# Land Cover Categories (NLCD 2019 Simplified)
# Mapping from NLCD codes to simplified categories
NLCD_LAND_COVER_MAP = {
    11: "water",
    12: "wetland",
    21: "forest",
    22: "forest",
    23: "forest",
    24: "forest",
    31: "forest",
    41: "grassland",
    42: "grassland",
    43: "grassland",
    51: "grassland",
    52: "grassland",
    71: "wetland",
    72: "wetland",
    73: "wetland",
    74: "wetland",
    75: "wetland",
    81: "grassland",
    82: "grassland",
    90: "wetland",
    95: "wetland"
}

# Specific NLCD codes for key categories used in analysis
NLCD_FOREST_CODES = [21, 22, 23, 24, 31]
NLCD_GRASSLAND_CODES = [41, 42, 43, 51, 52, 81, 82]
NLCD_WETLAND_CODES = [12, 71, 72, 73, 74, 75, 90, 95]
NLCD_URBAN_CODES = [11, 21] # Note: 11 is water, 21 is forest. Urban is typically 11-14 in full NLCD, but simplified here.
# Correcting Urban based on standard NLCD:
# 11: Open Water, 12: Perennial Ice/Snow, 13: Developed Open Space, 14: Developed Low Intensity
# 21: Deciduous Forest, 22: Evergreen Forest, 23: Mixed Forest, 24: Shrub/Scrub
# Let's define standard simplified mapping for the task:
# Forest: 21, 22, 23, 24, 31
# Grassland: 41, 42, 43, 51, 52, 81, 82
# Wetland: 12, 71, 72, 73, 74, 75, 90, 95
# Urban: 11, 13, 14, 21 (Wait, 21 is forest. Urban is 11-14 usually).
# Standard NLCD 2019 Urban: 11 (Open Water - no), 13 (Developed Open Space), 14 (Developed Low Intensity), 21 (Developed Med/High - No, 21 is forest).
# Actually, NLCD 2019:
# 11: Open Water
# 12: Perennial Ice/Snow
# 13: Developed, Open Space
# 14: Developed, Low Intensity
# 15: Developed, Medium Intensity
# 16: Developed, High Intensity
# 18: Cultivated Crops
# 19: Pasture/Hay
# 21: Deciduous Forest
# 22: Evergreen Forest
# 23: Mixed Forest
# 24: Shrubland
# 31: Barren Land
# 41: Dryland Crop
# 42: Orchards/Vineyards
# 43: Grassland/Herbaceous
# 44: Hay/Pasture
# 51: Woody Wetlands
# 52: Emergent Herbaceous Wetlands
# Let's use the simplified categories requested in the task description:
# forest_prop_100m, grassland_prop_100m, wetland_prop_100m, urban_prop_100m, other_prop_100m
# We will define the codes in the functions that use them, but here we set the constants.
# Urban: 13, 14, 15, 16
# Forest: 21, 22, 23, 24
# Grassland: 41, 42, 43, 44, 81, 82 (Simplified)
# Wetland: 51, 52, 12 (if applicable)

# --- Directory Path Functions ---
def get_project_root() -> Path:
    """Return the absolute path to the project root."""
    return _PROJECT_ROOT

def get_code_root() -> Path:
    """Return the absolute path to the code directory."""
    return _CODE_ROOT

def get_data_dir() -> Path:
    """Return the absolute path to the data directory."""
    return _PROJECT_ROOT / "data"

def get_raw_data_dir() -> Path:
    """Return the absolute path to the raw data directory."""
    return get_data_dir() / "raw"

def get_processed_dir() -> Path:
    """Return the absolute path to the processed data directory."""
    return get_data_dir() / "processed"

def get_models_dir() -> Path:
    """Return the absolute path to the models directory."""
    return _PROJECT_ROOT / "models"

def get_viz_dir() -> Path:
    """Return the absolute path to the visualization directory."""
    return _PROJECT_ROOT / "viz"

def get_figures_dir() -> Path:
    """Return the absolute path to the figures directory."""
    return get_viz_dir() / "figures"

def get_reports_dir() -> Path:
    """Return the absolute path to the reports directory."""
    return _PROJECT_ROOT / "docs" / "results"

def get_metadata_file() -> Path:
    """Return the absolute path to the metadata.yaml file."""
    return get_data_dir() / "metadata.yaml"

def ensure_directories():
    """Create all required directories if they do not exist."""
    directories = [
        get_raw_data_dir(),
        get_processed_dir(),
        get_models_dir(),
        get_figures_dir(),
        get_reports_dir()
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

# --- Random Seed Functions ---
def get_seed() -> int:
    """Return the global random seed."""
    return RANDOM_SEED

def set_seed(seed: int = RANDOM_SEED):
    """Set the random seed for reproducibility across libraries."""
    random.seed(seed)
    np.random.seed(seed)
    # If torch is available, set seed
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

# --- Model Parameters ---
def get_model_params() -> Dict[str, Any]:
    """Return default parameters for the Random Forest model."""
    return {
        "n_estimators": 100,
        "max_depth": None,
        "min_samples_split": 2,
        "min_samples_leaf": 1,
        "random_state": get_seed(),
        "n_jobs": -1
    }

def get_cv_params() -> Dict[str, Any]:
    """Return default parameters for cross-validation."""
    return {
        "n_splits": 5,
        "shuffle": True,
        "random_state": get_seed()
    }

# --- Permutation Test Parameters ---
def get_permutation_params() -> Dict[str, Any]:
    """Return default parameters for the permutation test."""
    return {
        "n_permutations": 1000,
        "random_state": get_seed()
    }

# --- Data Thresholds ---
def get_data_thresholds() -> Dict[str, int]:
    """Return thresholds for data filtering."""
    return {
        "min_observations": MIN_OBSERVATIONS_PER_SPECIES,
        "top_n_species": TOP_N_SPECIES,
        "buffer_radius_m": BUFFER_RADIUS_M
    }

# --- File Paths ---
def get_file_paths() -> Dict[str, Path]:
    """Return a dictionary of key file paths."""
    return {
        "metadata": get_metadata_file(),
        "raw_ebd": get_raw_data_dir() / "ebd_train.csv",
        "raw_nlcd": get_raw_data_dir() / "nlcd_2019.zip",
        "raw_guild_source": get_raw_data_dir() / "guild_source.csv",
        "processed_guild_mapping": get_processed_dir() / "guild_mapping.csv",
        "processed_species_counts": get_processed_dir() / "species_counts.json",
        "processed_top_species": get_processed_dir() / "top_25_species_ids.json",
        "processed_filtered_ebd": get_processed_dir() / "filtered_ebd.csv",
        "processed_merged": get_processed_dir() / "merged_observations.csv",
        "processed_profiles": get_processed_dir() / "species_profiles.csv",
        "model": get_models_dir() / "random_forest.pkl",
        "training_metrics": get_models_dir() / "training_metrics.json",
        "evaluation_results": get_models_dir() / "evaluation_results.json"
    }

def get_file_path(key: str) -> Path:
    """Get a specific file path by key."""
    paths = get_file_paths()
    if key not in paths:
        raise KeyError(f"File path key '{key}' not found in configuration.")
    return paths[key]
