import os
from pathlib import Path
from typing import Dict, Any, Optional
import json

# Project configuration constants
PROJECT_NAME = "llmXive-follow-up-extending-evalverse-pi"
PROJECT_VERSION = "0.1.0"
PYTHON_VERSION = "3.11"

# Random seeds for reproducibility
DEFAULT_SEED = 42

# Feature sufficiency threshold
FEATURE_SUFFICIENCY_THRESHOLD = 0.85

# VLM required threshold (lower 95% CI)
VLM_REQUIRED_THRESHOLD = 0.70

# Error rate threshold for sample exclusion
ERROR_RATE_THRESHOLD = 0.05

# Memory constraint for feasibility (GB)
MAX_MEMORY_GB = 7.0

# Time constraint for feasibility (hours)
MAX_TOTAL_HOURS = 6.0

# Evaluation subset size for validation gate
VALIDATION_SUBSET_SIZE = 30

# Permutation test iterations
PERMUTATION_ITERATIONS = 1000

# Thresholds for sensitivity analysis
SENSITIVITY_THRESHOLDS = [0.80, 0.85, 0.90]

def get_project_root() -> Path:
    """Get the project root directory."""
    # Assume src/config.py is at code/src/config.py, project root is code/
    current_file = Path(__file__).resolve()
    return current_file.parent.parent

def get_data_root() -> Path:
    """Get the data root directory."""
    return get_project_root() / "data"

def get_state_root() -> Path:
    """Get the state root directory."""
    return get_data_root() / "state"

def get_reports_root() -> Path:
    """Get the reports root directory."""
    return get_data_root() / "reports"

def get_figures_root() -> Path:
    """Get the figures root directory."""
    return get_data_root() / "figures"

def get_raw_data_dir() -> Path:
    """Get the raw data directory."""
    return get_data_root() / "raw"

def get_processed_data_dir() -> Path:
    """Get the processed data directory."""
    return get_data_root() / "processed"

def get_cache_dir() -> Path:
    """Get the cache directory."""
    return get_data_root() / "cache"

def ensure_environment() -> bool:
    """
    Ensure the project environment is properly configured.
    
    Creates necessary directories and validates paths.
    
    Returns:
        True if environment is ready, False otherwise.
    """
    try:
        # Create data directories
        data_root = get_data_root()
        data_root.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        dirs = [
            get_raw_data_dir(),
            get_processed_data_dir(),
            get_state_root(),
            get_reports_root(),
            get_figures_root(),
            get_cache_dir(),
        ]
        
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
        
        # Validate we can write to each directory
        for d in dirs:
            test_file = d / ".env_test"
            try:
                test_file.touch()
                test_file.unlink()
            except (OSError, PermissionError):
                return False
        
        return True
    except Exception as e:
        print(f"Environment setup failed: {e}")
        return False

def get_config_summary() -> Dict[str, Any]:
    """
    Get a summary of the current configuration.
    
    Returns:
        Dict containing configuration details.
    """
    return {
        "project_name": PROJECT_NAME,
        "project_version": PROJECT_VERSION,
        "python_version": PYTHON_VERSION,
        "default_seed": DEFAULT_SEED,
        "feature_sufficiency_threshold": FEATURE_SUFFICIENCY_THRESHOLD,
        "vlm_required_threshold": VLM_REQUIRED_THRESHOLD,
        "error_rate_threshold": ERROR_RATE_THRESHOLD,
        "max_memory_gb": MAX_MEMORY_GB,
        "max_total_hours": MAX_TOTAL_HOURS,
        "validation_subset_size": VALIDATION_SUBSET_SIZE,
        "permutation_iterations": PERMUTATION_ITERATIONS,
        "sensitivity_thresholds": SENSITIVITY_THRESHOLDS,
        "paths": {
            "project_root": str(get_project_root()),
            "data_root": str(get_data_root()),
            "state_root": str(get_state_root()),
            "reports_root": str(get_reports_root()),
            "figures_root": str(get_figures_root()),
            "raw_data": str(get_raw_data_dir()),
            "processed_data": str(get_processed_data_dir()),
            "cache": str(get_cache_dir()),
        }
    }
