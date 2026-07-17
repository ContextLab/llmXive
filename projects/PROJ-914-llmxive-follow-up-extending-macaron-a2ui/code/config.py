"""
Configuration module for llmXive follow-up: extending Macaron-A2UI.

This module centralizes all seeds, paths, and constants used across the project.
It ensures reproducibility and consistent directory structure handling.
"""

import os
from pathlib import Path
from typing import Final

# ============================================================================
# Project Root & Directory Constants
# ============================================================================

# Determine project root relative to this file's location
# Assuming structure: code/config.py -> project root is parent of 'code'
_PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent

# Standard directories
CODE_DIR: Final[Path] = _PROJECT_ROOT / "code"
DATA_DIR: Final[Path] = _PROJECT_ROOT / "data"
TESTS_DIR: Final[Path] = _PROJECT_ROOT / "tests"
SPECS_DIR: Final[Path] = _PROJECT_ROOT / "specs"
STATE_DIR: Final[Path] = _PROJECT_ROOT / "state"
FIGURES_DIR: Final[Path] = _PROJECT_ROOT / "figures"
MODELS_DIR: Final[Path] = _PROJECT_ROOT / "code" / "models"

# Specific data subdirectories
RAW_DATA_DIR: Final[Path] = DATA_DIR / "raw"
PROCESSED_DATA_DIR: Final[Path] = DATA_DIR / "processed"
ANNOTATED_DATA_DIR: Final[Path] = DATA_DIR / "annotated"
HOLDOUT_DATA_DIR: Final[Path] = DATA_DIR / "holdout"

# Specific model directories
ROUTER_MODEL_DIR: Final[Path] = MODELS_DIR / "router_model"
FALLBACK_ONTOLOGY_PATH: Final[Path] = CODE_DIR / "models" / "ontology.json"

# ============================================================================
# Reproducibility Seeds
# ============================================================================

RANDOM_SEED: Final[int] = 42
NumpyRandomSeed: Final[int] = 42
TorchRandomSeed: Final[int] = 42

# ============================================================================
# Dataset & Ingestion Constants
# ============================================================================

# HuggingFace Dataset Identifier for Macaron-A2UI (A2UI-Bench)
# Using the specific dataset ID mentioned in the project context
HF_DATASET_NAME: Final[str] = "macaron-a2ui/a2ui-bench"

# Filenames for processed data
RAW_CSV_FILENAME: Final[str] = "raw_a2ui_bench.csv"
ANNOTATED_CSV_FILENAME: Final[str] = "labeled_turns_n500.csv"
HOLDOUT_CSV_FILENAME: Final[str] = "holdout_set_n50.csv"
SIMULATION_LOG_FILENAME: Final[str] = "simulation_run_log.jsonl"
METRICS_OUTPUT_FILENAME: Final[str] = "alignment_metrics.csv"

# ============================================================================
# Simulation & Routing Parameters
# ============================================================================

# Router Configuration
ROUTER_MODEL_NAME: Final[str] = "distilbert-base-uncased"
ROUTER_CONFIDENCE_THRESHOLD: Final[float] = 0.75

# Simulation Parameters
MAX_USER_PATIENCE_MEAN: Final[float] = 2.0  # Mean for exponential decay (seconds)
LATENCY_INJECTION_STEPS: Final[list[float]] = [0.0, 0.5, 1.0, 2.0, 4.0]

# Information Density Levels for Fallback
DENSITY_LEVELS: Final[list[int]] = [1, 3, 5, 10]

# Rubric Weights (FR-005, SC-002)
RUBRIC_WEIGHT_INTENT_MATCH: Final[float] = 0.4
RUBRIC_WEIGHT_LATENCY_PENALTY: Final[float] = 0.3
RUBRIC_WEIGHT_UI_COMPLETENESS: Final[float] = 0.3

# ============================================================================
# Statistical Analysis Parameters
# ============================================================================

# Significance level for tests
ALPHA: Final[float] = 0.05
CORRECTION_METHOD: Final[str] = "fdr_bh"  # Benjamini-Hochberg FDR

# ============================================================================
# Logging & Versioning
# ============================================================================

LOG_LEVEL: Final[str] = "INFO"
LOG_FORMAT: Final[str] = "json"
STATE_FILE_PATH: Final[Path] = STATE_DIR / "version_state.yaml"

# ============================================================================
# Helper Functions for Path Resolution
# ============================================================================

def get_raw_data_path(filename: str | None = None) -> Path:
    """Get path to raw data directory or specific file."""
    if filename:
        return RAW_DATA_DIR / filename
    return RAW_DATA_DIR

def get_processed_data_path(filename: str | None = None) -> Path:
    """Get path to processed data directory or specific file."""
    if filename:
        return PROCESSED_DATA_DIR / filename
    return PROCESSED_DATA_DIR

def get_annotated_data_path(filename: str | None = None) -> Path:
    """Get path to annotated data directory or specific file."""
    if filename:
        return ANNOTATED_DATA_DIR / filename
    return ANNOTATED_DATA_DIR

def get_holdout_data_path(filename: str | None = None) -> Path:
    """Get path to holdout data directory or specific file."""
    if filename:
        return HOLDOUT_DATA_DIR / filename
    return HOLDOUT_DATA_DIR

def get_figures_path(filename: str | None = None) -> Path:
    """Get path to figures directory or specific file."""
    if filename:
        return FIGURES_DIR / filename
    return FIGURES_DIR

def ensure_dirs() -> None:
    """Ensure all required project directories exist."""
    directories = [
        CODE_DIR,
        DATA_DIR,
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        ANNOTATED_DATA_DIR,
        HOLDOUT_DATA_DIR,
        TESTS_DIR,
        SPECS_DIR,
        STATE_DIR,
        FIGURES_DIR,
        MODELS_DIR,
        ROUTER_MODEL_DIR,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

# Initialize directories on import to ensure structure exists
# This is safe as it only creates directories if they don't exist.
try:
    ensure_dirs()
except PermissionError:
    # If running in a restricted environment, we proceed but warn
    import warnings
    warnings.warn("Could not ensure project directories. Running in read-only mode.")