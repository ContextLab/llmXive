"""
Configuration management for the Plant Disease Severity Prediction project.

This module centralizes all project paths, random seeds, API keys,
and constant definitions to ensure reproducibility and ease of maintenance.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

# ============================================================================
# Project Root and Directory Structure
# ============================================================================

# Determine the project root relative to this file (code/config.py)
_CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = _CURRENT_FILE.parent.parent

# Subdirectories
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
TESTS_DIR = PROJECT_ROOT / "tests"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
SPECS_DIR = PROJECT_ROOT / "specs"
STATE_DIR = PROJECT_ROOT / "state"
FIGURES_DIR = DATA_DIR / "figures"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"
CONTRACTS_DIR = SPECS_DIR / "001-predict-plant-disease-severity" / "contracts"

# Ensure directories exist
def ensure_dirs():
    """Create all necessary directories if they do not exist."""
    for d in [DATA_DIR, TESTS_DIR, ARTIFACTS_DIR, STATE_DIR, FIGURES_DIR, PROCESSED_DIR, RAW_DIR, CONTRACTS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

# ============================================================================
# Random Seeds and Reproducibility
# ============================================================================

# Global random seed for reproducibility across numpy, random, torch (if used), etc.
RANDOM_SEED: int = 42

# ============================================================================
# API Keys and External Services
# ============================================================================

# Open-Meteo API (No key required, but rate limits apply)
OPEN_METEO_BASE_URL: str = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_HISTORICAL_URL: str = "https://archive-api.open-meteo.com/v1/archive"

# NOAA API (Optional fallback)
# Note: NOAA requires an API key for some endpoints. If not set, the system
# will attempt to use public endpoints or fail loudly as per FR-002.
NOAA_API_KEY: Optional[str] = os.getenv("NOAA_API_KEY", None)
NOAA_BASE_URL: str = "https://www.ncei.noaa.gov/access/services/data/v1"

# PlantVillage Dataset Source
# Using HuggingFace Datasets as the primary source for PlantVillage
PLANT_VILLAGE_DATASET_ID: str = "plantvillage"
PLANT_VILLAGE_HF_REPO: str = "plantvillage/dataset" # If a specific HF repo is used, otherwise standard load

# ============================================================================
# Data Processing Constants
# ============================================================================

# Image Processing
IMAGE_TARGET_SIZE: tuple = (256, 256)  # (width, height)
IMAGE_GRAYSCALE: bool = True  # For texture entropy calculation
COLOR_SPACE: str = "LAB"  # Color space for necrosis analysis (L*a*b*)

# Weather Aggregation
WEATHER_HISTORY_DAYS: int = 7  # Lookback period for weather features
WEATHER_AGGREGATION_METHODS: list = ["mean", "max", "min", "sum"]

# Data Validation
VALIDITY_CHECK_SAMPLE_SIZE: int = 50

# ============================================================================
# Modeling Constants
# ============================================================================

# Random Forest Parameters
RF_N_ESTIMATORS: int = 100
RF_MAX_DEPTH: int = None
RF_MIN_SAMPLES_SPLIT: int = 2
RF_MIN_SAMPLES_LEAF: int = 1
RF_N_JOBS: int = -1  # Use all available cores

# Permutation Test
PERMUTATION_ITERATIONS: int = 1000
PERMUTATION_RANDOM_SEED: int = RANDOM_SEED

# Train/Test Split
TEST_SIZE: float = 0.2
VALIDATION_SIZE: float = 0.1

# ============================================================================
# Output File Paths
# ============================================================================

# Data Outputs
UNIFIED_DATASET_PATH: Path = PROCESSED_DIR / "unified_analysis.csv"
DROPPED_RECORDS_LOG_PATH: Path = PROCESSED_DIR / "dropped_records.log"

# Model Outputs
MODEL_RESULTS_PATH: Path = ARTIFACTS_DIR / "results.json"
MODEL_STATE_PATH: Path = STATE_DIR / "model_state.yaml"

# Visualization Outputs
PDP_PLOTS_PATH: Path = FIGURES_DIR / "partial_dependence_plots.png"
SENSITIVITY_REPORT_PATH: Path = ARTIFACTS_DIR / "sensitivity_analysis.json"

# State Management
STATE_FILE_PATH: Path = STATE_DIR / "pipeline_state.yaml"

# ============================================================================
# Logging Configuration
# ============================================================================

LOG_LEVEL: str = "INFO"
LOG_FILE_PATH: Path = PROJECT_ROOT / "logs" / "pipeline.log"

# ============================================================================
# Helper Functions
# ============================================================================

def get_path(path_key: str) -> Path:
    """
    Retrieve a path by key name from this module's globals.
    Raises KeyError if the key is not found.
    """
    val = globals().get(path_key)
    if isinstance(val, Path):
        return val
    raise KeyError(f"Path key '{path_key}' not found in config or is not a Path.")

def get_env_or_fail(var_name: str, description: str) -> str:
    """
    Retrieve an environment variable. If missing, raise a clear error.
    Used for mandatory API keys.
    """
    val = os.getenv(var_name)
    if val is None:
        raise RuntimeError(f"Mandatory environment variable '{var_name}' is not set. {description}")
    return val

# Initialize directories on import if needed (optional, can be called explicitly)
# ensure_dirs()