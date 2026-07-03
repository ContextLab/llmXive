"""
Environment configuration for the llmXive research pipeline.

This module centralizes configuration settings including API keys,
file paths, random seeds, and runtime parameters.

It supports loading from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any

# Project Root
# Determine project root relative to this file (src/config.py)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ======================================================================
# Paths
# ======================================================================

class Paths:
    """Centralized file system paths."""
    
    PROJECT_ROOT: Path = _PROJECT_ROOT
    DATA_RAW: Path = PROJECT_ROOT / "data" / "raw"
    DATA_PROCESSED: Path = PROJECT_ROOT / "data" / "processed"
    DATA_VALIDATION: Path = PROJECT_ROOT / "data" / "validation"
    DATA_VALIDATION_EXTERNAL: Path = DATA_VALIDATION / "external"
    CODE_DIR: Path = PROJECT_ROOT / "code"
    SCRIPTS_DIR: Path = PROJECT_ROOT / "scripts"
    TESTS_DIR: Path = PROJECT_ROOT / "tests"
    NOTEBOOKS_DIR: Path = PROJECT_ROOT / "notebooks"
    FIGURES_DIR: Path = PROJECT_ROOT / "figures"
    STATE_DIR: Path = PROJECT_ROOT / "state" / "projects" / "PROJ-209-quantifying-the-influence-of-topological"
    
    # Specific file paths
    PRISTINE_STRUCTURES_CSV: Path = DATA_RAW / "pristine_structures.csv"
    DEFECT_DATASET_2022_CSV: Path = DATA_RAW / "defect_dataset_2022.csv"
    SYNTHETIC_TRAIN_CSV: Path = DATA_RAW / "synthetic_train.csv"
    SYNTHETIC_HOLDOUT_CSV: Path = DATA_RAW / "synthetic_holdout.csv"
    SYNTHETIC_FALLBACK_CSV: Path = DATA_RAW / "synthetic_defect_fallback.csv"
    FEATURES_CSV: Path = DATA_PROCESSED / "features.csv"
    TARGETS_CSV: Path = DATA_PROCESSED / "targets.csv"
    FEATURE_SELECTION_LOG_JSON: Path = DATA_PROCESSED / "feature_selection_log.json"
    MODELS_DIR: Path = DATA_PROCESSED / "models"
    VALIDATION_REPORT_JSON: Path = DATA_VALIDATION / "Validation_Report.json"
    EXTERNAL_DATA_ID: str = "exp_defect_graphene_mos2_v1"
    
    # Ensure directories exist on initialization
    @classmethod
    def ensure_directories(cls):
        """Create all required directories if they don't exist."""
        dirs = [
            cls.DATA_RAW, cls.DATA_PROCESSED, cls.DATA_VALIDATION,
            cls.DATA_VALIDATION_EXTERNAL, cls.CODE_DIR, cls.SCRIPTS_DIR,
            cls.TESTS_DIR, cls.NOTEBOOKS_DIR, cls.FIGURES_DIR, cls.STATE_DIR,
            cls.MODELS_DIR
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

# ======================================================================
# API Keys & External Services
# ======================================================================

class APIKeys:
    """External service credentials."""
    
    # Materials Project API
    # Required for T010: Query Materials Project REST API
    MATERIALS_PROJECT_API_KEY: str = os.getenv("MP_API_KEY", "")
    
    # Add other API keys here as needed
    # e.g., AWS_ACCESS_KEY, etc.

# ======================================================================
# Random Seeds & Reproducibility
# ======================================================================

class Seeds:
    """Random seeds for reproducibility across the pipeline."""
    
    # Default seed used across all tasks (T013, T021, etc.)
    GLOBAL_SEED: int = 42
    
    # Specific seeds for hold-out sets to ensure distinctness
    HOLDOUT_SEED: int = 123
    
    # Ensure reproducibility in numpy, random, etc.
    @classmethod
    def set_all(cls):
        """Set global seeds for numpy and python random."""
        import random
        import numpy as np
        random.seed(cls.GLOBAL_SEED)
        np.random.seed(cls.GLOBAL_SEED)

# ======================================================================
# Hyperparameters & Model Settings
# ======================================================================

class ModelSettings:
    """Default hyperparameters for modeling tasks."""
    
    # Random Forest
    RF_N_ESTIMATORS: int = 100
    RF_MAX_DEPTH: int = None
    RF_MIN_SAMPLES_SPLIT: int = 2
    RF_MIN_SAMPLES_LEAF: int = 1
    RF_RANDOM_STATE: int = Seeds.GLOBAL_SEED
    
    # Cross-Validation
    CV_FOLDS: int = 5
    
    # Permutation Importance
    PERMUTATION_N_REPETITIONS: int = 10
    
    # FDR Control
    FDR_ALPHA: float = 0.05
    
    # Ridge Regression (for collinearity handling)
    RIDGE_ALPHA: float = 1.0
    
    # VIF Threshold for exclusion
    VIF_THRESHOLD: float = 5.0

# ======================================================================
# Data Acquisition Settings
# ======================================================================

class DataAcquisition:
    """Settings for data fetching and generation."""
    
    # Materials Project Query
    MP_MIN_STRUCTURE_COUNT: int = 50
    MP_TARGET_MATERIALS: list = ["graphene", "MoS2"]
    
    # Synthetic Generation
    SYNTHETIC_MIN_ENTRIES: int = 100
    DEFECT_DENSITY_MIN: float = 0.001
    DEFECT_DENSITY_MAX: float = 0.1
    
    # Retry Logic (T009, T015)
    MAX_RETRIES: int = 5
    INITIAL_RETRY_DELAY: float = 1.0  # seconds
    MAX_RETRY_DELAY: float = 60.0
    BACKOFF_MULTIPLIER: float = 2.0

# ======================================================================
# Validation & Testing Settings
# ======================================================================

class Validation:
    """Settings for validation and CI."""
    
    # Runtime limits (seconds)
    MAX_WORKFLOW_RUNTIME_SECONDS: int = 6 * 3600  # 6 hours
    MAX_MOCK_DFTB_PLUS_RUNTIME_SECONDS: int = 300
    
    # Memory limits (GB) - for CI monitoring
    MAX_MEMORY_GB: int = 7

# ======================================================================
# Logging Settings
# ======================================================================

class Logging:
    """Logging configuration defaults."""
    
    LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

# ======================================================================
# Convenience Functions
# ======================================================================

def get_project_root() -> Path:
    """Return the project root directory."""
    return Paths.PROJECT_ROOT

def get_api_key(service: str) -> Optional[str]:
    """
    Retrieve an API key for a specific service.
    
    Args:
        service: Name of the service (e.g., 'materials_project')
        
    Returns:
        The API key string or None if not found.
    """
    if service.lower() == 'materials_project':
        return APIKeys.MATERIALS_PROJECT_API_KEY
    return None

def validate_config() -> Dict[str, Any]:
    """
    Validate that critical configuration is present.
    
    Returns:
        A dictionary with validation results.
    """
    issues = []
    
    # Check if MP API key is set (required for T010)
    if not APIKeys.MATERIALS_PROJECT_API_KEY:
        # It's optional if we fall back to synthetic, but warn
        issues.append("WARNING: MP_API_KEY not set. Data acquisition will rely on synthetic fallback.")
    
    # Check directories
    try:
        Paths.ensure_directories()
    except Exception as e:
        issues.append(f"ERROR: Could not create directories: {e}")
    
    return {
        "valid": len([i for i in issues if i.startswith("ERROR")]) == 0,
        "warnings": [i for i in issues if i.startswith("WARNING")],
        "errors": [i for i in issues if i.startswith("ERROR")]
    }