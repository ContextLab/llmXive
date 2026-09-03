"""
Configuration module for the Avian Foraging Behavior prediction pipeline.
Defines paths, random seeds, and constants used across the project.
"""
import os
import random
from pathlib import Path
from typing import Dict, Any, Optional, List
import numpy as np

# --- Constants ---
RANDOM_SEED = 42
BUFFER_RADIUS_M = 100  # meters
MIN_OBSERVATIONS_PER_SPECIES = 50
MAX_TOP_SPECIES_COUNT = 25
NLCD_YEAR = 2019
NLCD_RESOLUTION = 30  # meters

# --- Project Paths ---
# The project root is assumed to be the parent of the 'code' directory
# or the directory containing this file's parent.
# We calculate it relative to this file's location.
_THIS_FILE_DIR = Path(__file__).resolve().parent
CODE_ROOT = _THIS_FILE_DIR.parent
PROJECT_ROOT = CODE_ROOT.parent

# --- Directory Getters ---
def get_project_root() -> Path:
    """Returns the root directory of the project."""
    return PROJECT_ROOT

def get_code_root() -> Path:
    """Returns the code/ directory."""
    return CODE_ROOT

def get_data_dir() -> Path:
    """Returns the data/ directory."""
    return PROJECT_ROOT / "data"

def get_raw_data_dir() -> Path:
    """Returns the data/raw/ directory."""
    return get_data_dir() / "raw"

def get_processed_dir() -> Path:
    """Returns the data/processed/ directory."""
    return get_data_dir() / "processed"

def get_models_dir() -> Path:
    """Returns the models/ directory (project root level, not code/models)."""
    # Based on T001b description: "projects/.../code/models/"
    # However, T019 says "save to data/models/random_forest.pkl"
    # And T001b says "Initialize `models/` directory... `projects/.../code/models/`"
    # Let's stick to the T001b definition for the code structure, but T019 might expect data/models.
    # The task T004 defines paths. T001b explicitly created code/models.
    # Let's provide both or clarify. T001b created code/models.
    # But T019 says "save to data/models".
    # Let's assume the standard structure:
    # Project Root
    #   data/
    #     raw/
    #     processed/
    #     models/ (for trained artifacts as per T019)
    #   code/
    #     models/ (source code)
    #
    # T019 says: "save the trained model to `data/models/random_forest.pkl`"
    # So we need a `get_models_dir()` that points to `data/models`.
    # And `get_code_models_dir()` if needed for source? No, source is just `code/models`.
    # Let's align with T019: models_dir = data/models
    return get_data_dir() / "models"

def get_viz_dir() -> Path:
    """Returns the viz/ directory (project root level, for output)."""
    # T001c: "Initialize `viz/` directory... `projects/.../code/viz/`"
    # T025: "Output filename: `docs/results/confusion_matrix.png`"
    # T027: "Save the final map to `docs/results/habitat_map.png`"
    # There is a discrepancy between T001c (code/viz) and T025/T027 (docs/results).
    # The task T004 defines paths. T001c created code/viz.
    # Let's assume the output directory is `docs/results` as per T025/T027.
    # But T001c created `code/viz`.
    # Let's provide `get_viz_dir()` as `PROJECT_ROOT / "docs" / "results"` to match T025.
    # And `get_code_viz_dir()` for the source code directory if needed.
    # Actually, T001c says "Initialize `viz/` directory... `projects/.../code/viz/`".
    # This suggests the source code for viz is in `code/viz`.
    # The output is in `docs/results`.
    # Let's define `get_viz_output_dir()` for the output.
    # And `get_code_viz_dir()` for the source.
    # But the function name `get_viz_dir` in the API surface suggests a single dir.
    # Let's look at the API surface: `get_viz_dir` is listed.
    # Let's assume `get_viz_dir` returns `PROJECT_ROOT / "docs" / "results"` as that's where outputs go.
    # And `get_code_viz_dir` is not in the API surface, so maybe `code/viz` is not used for output.
    # Let's stick to `docs/results` for `get_viz_dir`.
    return PROJECT_ROOT / "docs" / "results"

def get_figures_dir() -> Path:
    """Returns the figures/ directory (if separate from viz output)."""
    # T001c created `code/viz`. T025 uses `docs/results`.
    # Let's assume `figures` is a subdirectory of `docs/results` or `data/figures`.
    # T001c says "Initialize `viz/` directory... `projects/.../code/viz/`".
    # Let's assume `get_figures_dir` returns `PROJECT_ROOT / "docs" / "results"`.
    return get_viz_dir()

def get_reports_dir() -> Path:
    """Returns the reports/ directory."""
    return PROJECT_ROOT / "docs" / "results"

def get_metadata_file() -> Path:
    """Returns the path to data/metadata.yaml."""
    return get_data_dir() / "metadata.yaml"

# --- Directory Creation ---
def ensure_directories():
    """Creates all required directories if they do not exist."""
    dirs = [
        get_data_dir(),
        get_raw_data_dir(),
        get_processed_dir(),
        get_models_dir(),
        get_viz_dir(),
        get_figures_dir(),
        get_reports_dir(),
        PROJECT_ROOT / "docs",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# --- Random Seed Management ---
def get_seed() -> int:
    """Returns the global random seed."""
    return RANDOM_SEED

def set_seed(seed: Optional[int] = None):
    """Sets the random seed for reproducibility."""
    if seed is None:
        seed = RANDOM_SEED
    random.seed(seed)
    np.random.seed(seed)

# --- Model & Training Parameters ---
def get_model_params() -> Dict[str, Any]:
    """Returns default parameters for the Random Forest model."""
    return {
        "n_estimators": 100,
        "max_depth": None,
        "min_samples_split": 2,
        "min_samples_leaf": 1,
        "random_state": RANDOM_SEED,
        "n_jobs": -1,
    }

def get_cv_params() -> Dict[str, Any]:
    """Returns default parameters for cross-validation."""
    return {
        "n_splits": 5,
        "shuffle": True,
        "random_state": RANDOM_SEED,
    }

def get_permutation_params() -> Dict[str, Any]:
    """Returns default parameters for the permutation test."""
    return {
        "n_permutations": 1000,
        "random_state": RANDOM_SEED,
    }

# --- Data Thresholds ---
def get_data_thresholds() -> Dict[str, int]:
    """Returns data filtering thresholds."""
    return {
        "min_observations": MIN_OBSERVATIONS_PER_SPECIES,
        "max_species": MAX_TOP_SPECIES_COUNT,
    }

# --- File Paths ---
def get_file_paths() -> Dict[str, Path]:
    """Returns a dictionary of important file paths."""
    return {
        "ebd_train": get_raw_data_dir() / "ebd_train.csv",
        "nlcd_2019": get_raw_data_dir() / "nlcd_2019.zip",
        "guild_source": get_raw_data_dir() / "guild_source.csv",
        "guild_mapping": get_processed_dir() / "guild_mapping.csv",
        "top_species": get_processed_dir() / "top_25_species_ids.json",
        "merged_observations": get_processed_dir() / "merged_observations.csv",
        "species_profiles": get_processed_dir() / "species_profiles.csv",
        "model": get_models_dir() / "random_forest.pkl",
        "metadata": get_metadata_file(),
    }

def get_file_path(name: str) -> Path:
    """Returns a specific file path by name."""
    paths = get_file_paths()
    if name not in paths:
        raise ValueError(f"Unknown file name: {name}")
    return paths[name]

# --- Initialization ---
# Ensure directories exist when the module is imported
# (Optional, but helpful for scripts that rely on these paths immediately)
# ensure_directories() # Commented out to avoid side effects on import, called explicitly in main() of scripts if needed.
