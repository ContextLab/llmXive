"""
Configuration module for the Avian Foraging Behavior Prediction Pipeline.

Defines project paths, random seeds, and constants.
"""
import os
import random
from pathlib import Path
from typing import Dict, Any, Optional, List
import numpy as np

# --- Global Constants & Seeds ---
RANDOM_SEED = 42
PROJECT_NAME = "PROJ-397-predicting-avian-foraging-behavior-from-"

# Land Cover Classes (NLCD 2019)
LAND_COVER_CLASSES = {
    11: "Open Water",
    12: "Perennial Ice/Snow",
    21: "Developed, Open Space",
    22: "Developed, Low Intensity",
    23: "Developed, Medium Intensity",
    24: "Developed, High Intensity",
    31: "Barren Land",
    41: "Deciduous Forest",
    42: "Evergreen Forest",
    43: "Mixed Forest",
    51: "Dwarf Scrub",
    52: "Shrub/Scrub",
    71: "Grassland/Herbaceous",
    72: "Sedge/Herbaceous",
    73: "Lichens",
    74: "Moss",
    81: "Pasture/Hay",
    82: "Cultivated Crops",
    90: "Woody Wetlands",
    95: "Emergent Herbaceous Wetlands"
}

# Aggregated Land Cover Categories for Modeling
LAND_COVER_GROUPINGS = {
    "forest": [41, 42, 43],
    "grassland": [71, 72, 73, 74, 81],
    "wetland": [90, 95],
    "urban": [21, 22, 23, 24],
    "other": [11, 12, 31, 51, 52, 82]
}

FORAGING_GUILDS = [
    "Ground-Foraging",
    "Canopy-Foraging",
    "Water-Foraging",
    "Snag-Foraging",
    "Trunk-Foraging",
    "Cavity-Foraging"
]

# --- Path Resolvers ---

def get_project_root() -> Path:
    """Return the absolute path to the project root."""
    # Assumes code/ is at the root of the repo structure as per T001
    current_file = Path(__file__).resolve()
    # Navigate up to the project root (code/utils/config.py -> code/utils -> code -> root)
    # Based on T001: projects/PROJ-397-.../code/
    return current_file.parent.parent.parent

def get_code_root() -> Path:
    """Return the path to the code/ directory."""
    return get_project_root() / "code"

def get_data_dir() -> Path:
    """Return the path to the data/ directory."""
    return get_project_root() / "data"

def get_raw_data_dir() -> Path:
    """Return the path to the data/raw/ directory."""
    return get_data_dir() / "raw"

def get_processed_dir() -> Path:
    """Return the path to the data/processed/ directory."""
    return get_data_dir() / "processed"

def get_models_dir() -> Path:
    """Return the path to the models/ directory."""
    return get_project_root() / "models"

def get_viz_dir() -> Path:
    """Return the path to the viz/ directory."""
    return get_project_root() / "viz"

def get_figures_dir() -> Path:
    """Return the path to the viz/figures/ directory."""
    return get_viz_dir() / "figures"

def get_reports_dir() -> Path:
    """Return the path to the viz/reports/ directory."""
    return get_viz_dir() / "reports"

def get_metadata_file() -> Path:
    """Return the path to the data/metadata.yaml file."""
    return get_data_dir() / "metadata.yaml"

# --- Seed Management ---

def get_seed() -> int:
    """Return the global random seed."""
    return RANDOM_SEED

def set_seed(seed: Optional[int] = None) -> None:
    """Set the random seed for reproducibility across libraries."""
    if seed is None:
        seed = RANDOM_SEED
    
    random.seed(seed)
    np.random.seed(seed)

# --- Parameter Getters ---

def get_land_cover_class_names() -> Dict[int, str]:
    """Return the mapping of NLCD class IDs to names."""
    return LAND_COVER_CLASSES

def get_foraging_guilds() -> List[str]:
    """Return the list of defined foraging guilds."""
    return FORAGING_GUILDS

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
    """Return default parameters for Cross-Validation."""
    return {
        "n_splits": 5,
        "shuffle": True,
        "random_state": get_seed()
    }

def get_permutation_params() -> Dict[str, Any]:
    """Return default parameters for the Permutation Test."""
    return {
        "n_iterations": 1000,
        "random_state": get_seed(),
        "alpha": 0.05
    }

def get_data_thresholds() -> Dict[str, Any]:
    """Return thresholds for data filtering."""
    return {
        "min_observations_per_species": 50,
        "top_species_count": 25,
        "buffer_radius_meters": 100
    }

def get_file_path(relative_path: str) -> Path:
    """Construct an absolute path from a relative path string."""
    return get_project_root() / relative_path

def get_file_paths() -> Dict[str, Path]:
    """Return a dictionary of common file paths."""
    return {
        "raw_ebd": get_raw_data_dir() / "ebd_train.parquet",
        "raw_nlcd": get_raw_data_dir() / "nlcd_2019.zip",
        "raw_guilds": get_raw_data_dir() / "guild_source.csv",
        "processed_guild_mapping": get_processed_dir() / "guild_mapping.csv",
        "processed_species_counts": get_processed_dir() / "species_counts.json",
        "processed_top_species": get_processed_dir() / "top_25_species_ids.json",
        "processed_filtered_ebd": get_processed_dir() / "filtered_ebd.csv",
        "processed_merged_observations": get_processed_dir() / "merged_observations.csv",
        "processed_species_profiles": get_processed_dir() / "species_profiles.csv",
        "model_file": get_models_dir() / "random_forest.pkl",
        "training_metrics": get_models_dir() / "training_metrics.json",
        "evaluation_results": get_models_dir() / "evaluation_results.json",
        "metadata": get_metadata_file()
    }

def ensure_directories() -> None:
    """Ensure all required directories exist."""
    dirs = [
        get_raw_data_dir(),
        get_processed_dir(),
        get_models_dir(),
        get_figures_dir(),
        get_reports_dir()
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# --- Utility for Logging ---
def get_logger(name: str = "pipeline") -> "logging.Logger":
    """Get a configured logger instance."""
    import logging
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger