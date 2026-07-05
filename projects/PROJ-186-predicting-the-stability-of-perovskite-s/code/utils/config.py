"""
Configuration module for the Perovskite Stability Prediction pipeline.

Contains hyperparameters, element sets for virtual screening, and API rate-limiting constants.
"""
from typing import Set, Dict, Any, List, Optional
import os
import json

# ----------------------------------------------------------------------
# API Rate Limiting Constants
# ----------------------------------------------------------------------
# Materials Project API rate limits (approximate)
# Docs: https://docs.materialsproject.org/methodology/faq
MP_API_BASE_URL: str = "https://api.materialsproject.org"
MP_API_KEY_ENV_VAR: str = "MP_API_KEY"

# Rate limiting configuration for requests
RATE_LIMIT_MAX_RETRIES: int = 5
RATE_LIMIT_INITIAL_DELAY: float = 1.0  # seconds
RATE_LIMIT_MAX_DELAY: float = 60.0     # seconds
RATE_LIMIT_BACKOFF_FACTOR: float = 2.0
RATE_LIMIT_STATUS_FORCELIST: List[int] = [429, 500, 502, 503, 504]

# ----------------------------------------------------------------------
# Element Sets for Virtual Screening (US3)
# ----------------------------------------------------------------------
# A-site elements: K, Rb, Cs, Ba, Sr (5 elements per plan.md Phase 3)
ELEMENTS_A_SITE: Set[str] = {"K", "Rb", "Cs", "Ba", "Sr"}

# B-site elements: Ti, Zr, Hf, Sn, Ge
ELEMENTS_B_SITE: Set[str] = {"Ti", "Zr", "Hf", "Sn", "Ge"}

# X-site elements (Halogens): F, Cl, Br, I
ELEMENTS_X_SITE: Set[str] = {"F", "Cl", "Br", "I"}

# Combined set for quick lookup
VALID_PEROVSKITE_ELEMENTS: Set[str] = ELEMENTS_A_SITE | ELEMENTS_B_SITE | ELEMENTS_X_SITE

# ----------------------------------------------------------------------
# Hyperparameters for Model Training (US2)
# ----------------------------------------------------------------------
# RandomForestRegressor GridSearchCV parameters
MODEL_GRID_SEARCH_PARAMS: Dict[str, List[Any]] = {
    "max_depth": [10, 15, 20],
    "min_samples_leaf": [1, 2, 4],
    "n_estimators": [100],  # Fixed for consistency, can be expanded
    "random_state": [42],
    "n_jobs": [-1]  # Use all available cores
}

# Cross-validation settings
CV_FOLDS: int = 5
TEST_SIZE: float = 0.2
STRATIFY_TARGET: str = "decomposition_energy_binned"  # If stratification is needed

# Performance thresholds
LOW_CONFIDENCE_RMSE_THRESHOLD: float = 0.15  # eV/atom (from SC-001)

# ----------------------------------------------------------------------
# Geometric Feasibility Filters (US3)
# ----------------------------------------------------------------------
# Goldschmidt tolerance factor (t) range
TOLERANCE_FACTOR_MIN: float = 0.8
TOLERANCE_FACTOR_MAX: float = 1.1

# Octahedral factor (mu) range (optional, often 0.44-0.90)
OCTAHEDRAL_FACTOR_MIN: float = 0.44
OCTAHEDRAL_FACTOR_MAX: float = 0.90

# ----------------------------------------------------------------------
# Data Processing Constants
# ----------------------------------------------------------------------
# Target column for stability
TARGET_COLUMN: str = "decomposition_energy"

# Structural space groups of interest (Cubic and Rhombohedral)
TARGET_SPACE_GROUPS: List[int] = [221, 148]

# Minimum entries required from initial fetch
MIN_VALID_ENTRIES_THRESHOLD: int = 5000

# ----------------------------------------------------------------------
# Path Constants
# ----------------------------------------------------------------------
PROJECT_ROOT: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR: str = os.path.join(PROJECT_ROOT, "data")
PROCESSED_DATA_DIR: str = os.path.join(DATA_DIR, "processed")
RESULTS_DIR: str = os.path.join(PROJECT_ROOT, "results")
LOGS_DIR: str = os.path.join(PROJECT_ROOT, "logs")
SPEC_DIR: str = os.path.join(PROJECT_ROOT, "specs")

# File paths
FEATURES_CSV_PATH: str = os.path.join(PROCESSED_DATA_DIR, "features.csv")
MODEL_PKL_PATH: str = os.path.join(RESULTS_DIR, "model.pkl")
METRICS_JSON_PATH: str = os.path.join(RESULTS_DIR, "metrics.json")
SCREENING_FULL_CSV_PATH: str = os.path.join(RESULTS_DIR, "screening_full.csv")
SCREENING_CANDIDATES_MD_PATH: str = os.path.join(RESULTS_DIR, "screening_candidates.md")
PIPELINE_LOG_PATH: str = os.path.join(LOGS_DIR, "pipeline.log")

# ----------------------------------------------------------------------
# Helper Functions
# ----------------------------------------------------------------------
def get_api_key() -> Optional[str]:
    """
    Retrieves the Materials Project API key from environment variables.
    
    Returns:
        str: The API key if found, None otherwise.
    """
    key = os.getenv(MP_API_KEY_ENV_VAR)
    if not key:
        raise ValueError(
            f"API key not found. Please set the {MP_API_KEY_ENV_VAR} environment variable."
        )
    return key

def get_config_summary() -> Dict[str, Any]:
    """
    Returns a summary of the current configuration for logging purposes.
    
    Returns:
        dict: A dictionary containing key configuration parameters.
    """
    return {
        "target_space_groups": TARGET_SPACE_GROUPS,
        "tolerance_factor_range": (TOLERANCE_FACTOR_MIN, TOLERANCE_FACTOR_MAX),
        "model_grid_params": MODEL_GRID_SEARCH_PARAMS,
        "cv_folds": CV_FOLDS,
        "test_size": TEST_SIZE,
        "low_confidence_threshold": LOW_CONFIDENCE_RMSE_THRESHOLD,
        "elements_a": len(ELEMENTS_A_SITE),
        "elements_b": len(ELEMENTS_B_SITE),
        "elements_x": len(ELEMENTS_X_SITE)
    }