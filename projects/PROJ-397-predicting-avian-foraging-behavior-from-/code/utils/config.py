"""
Configuration module for the Avian Foraging Behavior Prediction Pipeline.

This module defines all project paths, random seeds, and global constants
used throughout the pipeline to ensure reproducibility and consistent
directory structure handling.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional

# ========================================================================
# Project Root and Directory Paths
# ========================================================================

# Determine the project root based on the current working directory or
# explicit environment variable. Defaults to the parent of the 'code' directory.
_CODE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = _CODE_DIR.parent if _CODE_DIR.name == "code" else _CODE_DIR

# Core subdirectories relative to code/
DATA_DIR = _CODE_DIR / "data"
MODELS_DIR = _CODE_DIR / "models"
VIZ_DIR = _CODE_DIR / "viz"
NOTEBOOKS_DIR = _CODE_DIR / "notebooks"
UTILS_DIR = _CODE_DIR / "utils"
TESTS_DIR = _CODE_DIR / "tests"

# Processed data subdirectories
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"
EXTERNAL_DIR = DATA_DIR / "external"

# Output directories for artifacts
FIGURES_DIR = VIZ_DIR / "figures"
REPORTS_DIR = _CODE_DIR / "docs" / "results"

# Ensure all required directories exist
_REQUIRED_DIRS = [
    DATA_DIR, RAW_DIR, PROCESSED_DIR, EXTERNAL_DIR,
    MODELS_DIR, VIZ_DIR, FIGURES_DIR,
    NOTEBOOKS_DIR, UTILS_DIR, TESTS_DIR, REPORTS_DIR
]

def _ensure_directories():
    """Create all required directories if they do not exist."""
    for dir_path in _REQUIRED_DIRS:
        dir_path.mkdir(parents=True, exist_ok=True)

# Initialize directories on import
_ensure_directories()


# ========================================================================
# Random Seeds and Reproducibility
# ========================================================================

# Global random seed for reproducibility across all libraries
RANDOM_SEED = 42

# Numpy random state
import numpy as np
np.random.seed(RANDOM_SEED)

# Standard library random state
import random
random.seed(RANDOM_SEED)

# Scikit-learn random state (used in models)
SKLEARN_RANDOM_STATE = RANDOM_SEED


# ========================================================================
# Data Constants and Thresholds
# ========================================================================

# Minimum number of observations required per species for statistical power
MIN_OBSERVATIONS_PER_SPECIES = 50

# Number of top species to select for analysis
TOP_N_SPECIES = 25

# Buffer radius (in meters) for land cover extraction around observation points
BUFFER_RADIUS_M = 100

# Target year for NLCD land cover data
NLCD_TARGET_YEAR = 2019

# eBird data version or release identifier (update as needed)
EBD_VERSION = "2023"

# Foraging guilds to be predicted (derived from guild_mapping.csv)
# Note: Actual guilds are loaded dynamically, but this defines the expected scope
EXPECTED_GUILDS = [
    "Insectivore", "Granivore", "Nectarivore", "Carnivore",
    "Omnivore", "Herbivore", "Scavenger", "Frugivore"
]


# ========================================================================
# Model Hyperparameters
# ========================================================================

# Random Forest Classifier defaults
RF_N_ESTIMATORS = 100
RF_MAX_DEPTH = None
RF_MIN_SAMPLES_SPLIT = 2
RF_MIN_SAMPLES_LEAF = 1
RF_MAX_FEATURES = "sqrt"
RF_CLASS_WEIGHT = "balanced"

# Cross-validation settings
CV_FOLDS = 5
CV_SHUFFLE = True

# Permutation test settings
PERMUTATION_ITERATIONS = 1000
PERMUTATION_ALPHA = 0.05


# ========================================================================
# File Paths and Filenames
# ========================================================================

# Input data filenames
EBD_RAW_FILENAME = "ebd_raw.csv"
NLCD_RAW_FILENAME = "nlcd_2019.tif"
GUILD_MAPPING_FILENAME = "guild_mapping.csv"

# Processed data filenames
EBD_TOP25_FILENAME = "ebd_top25.csv"
MERGED_OBSERVATIONS_FILENAME = "merged_observations.csv"
EXCLUDED_SPECIES_LOG_FILENAME = "excluded_species.log"
SPECIES_PROFILES_FILENAME = "species_profiles.csv"
TOP_SPECIES_JSON_FILENAME = "top_species.json"

# Model artifacts
MODEL_FILENAME = "random_forest_model.pkl"
MODEL_METRICS_FILENAME = "model_metrics.json"

# Visualization outputs
CONFUSION_MATRIX_FILENAME = "confusion_matrix.png"
FEATURE_IMPORTANCE_FILENAME = "feature_importance.png"
HABITAT_MAP_FILENAME = "habitat_map.geojson"
HABITAT_MAP_PNG_FILENAME = "habitat_map.png"

# Reports
FEATURE_IMPORTANCE_REPORT_FILENAME = "feature_importance_report.md"

# Metadata and logs
METADATA_FILENAME = "metadata.yaml"
PROVENANCE_FILENAME = "provenance.json"
PIPELINE_LOG_FILENAME = "pipeline.log"


# ========================================================================
# URL Constants for Data Sources
# ========================================================================

# eBird Basic Dataset (EBD) download URL
# Note: This is a placeholder; actual URL should be fetched from eBird website or S3
EBD_DOWNLOAD_URL = "https://ebird.org/static/ebd/ebd_relMay2023.zip"

# NLCD 2019 Land Cover download URL (USGS)
NLCD_DOWNLOAD_URL = "https://www.mrlc.gov/data/nlcd_2019_land_cover_48_state_20190603.zip"

# Guild mapping source (Cornell Lab of Ornithology)
GUILD_MAPPING_URL = "https://birdsoftheworld.org/bow/species/ebird-guilds.csv"


# ========================================================================
# Logging Configuration
# ========================================================================

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


# ========================================================================
# Utility Functions
# ========================================================================

def get_project_root() -> Path:
    """Return the project root directory."""
    return PROJECT_ROOT

def get_data_dir() -> Path:
    """Return the data directory."""
    return DATA_DIR

def get_processed_dir() -> Path:
    """Return the processed data directory."""
    return PROCESSED_DIR

def get_models_dir() -> Path:
    """Return the models directory."""
    return MODELS_DIR

def get_viz_dir() -> Path:
    """Return the visualization directory."""
    return VIZ_DIR

def get_figures_dir() -> Path:
    """Return the figures directory."""
    return FIGURES_DIR

def get_reports_dir() -> Path:
    """Return the reports directory."""
    return REPORTS_DIR

def get_seed() -> int:
    """Return the global random seed."""
    return RANDOM_SEED

def get_model_params() -> Dict[str, Any]:
    """Return default Random Forest hyperparameters."""
    return {
        "n_estimators": RF_N_ESTIMATORS,
        "max_depth": RF_MAX_DEPTH,
        "min_samples_split": RF_MIN_SAMPLES_SPLIT,
        "min_samples_leaf": RF_MIN_SAMPLES_LEAF,
        "max_features": RF_MAX_FEATURES,
        "class_weight": RF_CLASS_WEIGHT,
        "random_state": SKLEARN_RANDOM_STATE
    }

def get_cv_params() -> Dict[str, Any]:
    """Return cross-validation parameters."""
    return {
        "n_splits": CV_FOLDS,
        "shuffle": CV_SHUFFLE,
        "random_state": SKLEARN_RANDOM_STATE
    }

def get_permutation_params() -> Dict[str, Any]:
    """Return permutation test parameters."""
    return {
        "n_iterations": PERMUTATION_ITERATIONS,
        "alpha": PERMUTATION_ALPHA
    }

def get_data_thresholds() -> Dict[str, int]:
    """Return data filtering thresholds."""
    return {
        "min_observations": MIN_OBSERVATIONS_PER_SPECIES,
        "top_n_species": TOP_N_SPECIES,
        "buffer_radius_m": BUFFER_RADIUS_M
    }

def get_file_paths() -> Dict[str, Path]:
    """Return all key file paths as a dictionary."""
    return {
        "ebd_raw": DATA_DIR / EBD_RAW_FILENAME,
        "nlcd_raw": DATA_DIR / NLCD_RAW_FILENAME,
        "guild_mapping": PROCESSED_DIR / GUILD_MAPPING_FILENAME,
        "ebd_top25": PROCESSED_DIR / EBD_TOP25_FILENAME,
        "merged_observations": PROCESSED_DIR / MERGED_OBSERVATIONS_FILENAME,
        "excluded_species_log": PROCESSED_DIR / EXCLUDED_SPECIES_LOG_FILENAME,
        "species_profiles": PROCESSED_DIR / SPECIES_PROFILES_FILENAME,
        "top_species_json": PROCESSED_DIR / TOP_SPECIES_JSON_FILENAME,
        "model": MODELS_DIR / MODEL_FILENAME,
        "model_metrics": MODELS_DIR / MODEL_METRICS_FILENAME,
        "confusion_matrix": FIGURES_DIR / CONFUSION_MATRIX_FILENAME,
        "feature_importance": FIGURES_DIR / FEATURE_IMPORTANCE_FILENAME,
        "habitat_map": FIGURES_DIR / HABITAT_MAP_FILENAME,
        "habitat_map_png": FIGURES_DIR / HABITAT_MAP_PNG_FILENAME,
        "feature_report": REPORTS_DIR / FEATURE_IMPORTANCE_REPORT_FILENAME,
        "metadata": DATA_DIR / METADATA_FILENAME,
        "provenance": DATA_DIR / PROVENANCE_FILENAME,
        "pipeline_log": DATA_DIR / PIPELINE_LOG_FILENAME
    }