"""
Configuration module for the Solar Irradiance Reconstruction project.
Provides path management, random seeds, and constants.

This module centralizes all project configuration including:
- Directory paths for data and code
- Random seeds for reproducibility
- Constants for gap filling logic (FR-002)
- Sensitivity analysis thresholds (FR-009)
"""
import os
from pathlib import Path
from typing import Final, List, Dict, Any
import logging

# Setup environment variables before defining paths
# Import from env_manager which is already in the API surface
try:
    from env_manager import setup_environment, get_data_path
except ImportError:
    # Fallback for testing if env_manager isn't fully set up yet
    setup_environment = lambda: None
    get_data_path = lambda: None

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure environment variables are loaded
setup_environment()

# ============================================================================
# PROJECT STRUCTURE
# ============================================================================

# Project root directory (parent of code/)
PROJECT_ROOT: Final[Path] = Path(__file__).parent.parent

# ============================================================================
# DATA DIRECTORIES
# ============================================================================

DATA_RAW_DIR: Final[Path] = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR: Final[Path] = PROJECT_ROOT / "data" / "processed"

# ============================================================================
# CODE DIRECTORIES
# ============================================================================

CODE_MODELS_DIR: Final[Path] = PROJECT_ROOT / "code" / "models"
CODE_ANALYSIS_DIR: Final[Path] = PROJECT_ROOT / "code" / "analysis"
CODE_DATA_DIR: Final[Path] = PROJECT_ROOT / "code" / "data"
CODE_MODELS_ARTIFACTS_DIR: Final[Path] = CODE_MODELS_DIR / "artifacts"

# ============================================================================
# RANDOM SEEDS
# ============================================================================

# Global random seed for reproducibility across all libraries
RANDOM_SEED: Final[int] = 42

# ============================================================================
# FR-002: GAP FILLING LOGIC
# ============================================================================

# Threshold for gap filling: gaps >= 1 year use TSI proxy
# 1 year in days (using 365.25 for leap year average)
GAP_THRESHOLD_DAYS: Final[int] = 365

# TSI proxy value for gaps >= 1 year (FR-002)
# NOT using GSN=0, but a constant TSI value
TSI_PROXY_VALUE: Final[float] = 1360.5  # W/m²

# ============================================================================
# FR-009: SENSITIVITY ANALYSIS THRESHOLDS
# ============================================================================

# Inconsistency tolerance thresholds for sensitivity analysis
# These values are swept to measure reconstruction stability
SENSITIVITY_THRESHOLDS: Final[List[float]] = [0.01, 0.05, 0.1]

# ============================================================================
# MODEL HYPERPARAMETERS
# ============================================================================

# Random Forest parameters (from T015)
RF_MAX_DEPTH: Final[int] = 10
RF_N_ESTIMATORS: Final[int] = 100

# Gaussian Process parameters
GP_KERNEL: Final[str] = "RBF"  # Radial Basis Function kernel

# ============================================================================
# BOOTSTRAP ANALYSIS
# ============================================================================

# Number of bootstrap iterations for variance estimation (FR-005)
BOOTSTRAP_ITERATIONS: Final[int] = 1000

# ============================================================================
# DATA SOURCES (URLs - managed via env_manager but defined here for reference)
# ============================================================================

# SILSO (Royal Observatory of Belgium) - Sunspot Number data
# URL should be configured via environment variable
SILSO_URL_ENV_VAR: Final[str] = "SILSO_URL"

# SORCE/TIM - Total Solar Irradiance data
# URL should be configured via environment variable
SORCE_URL_ENV_VAR: Final[str] = "SORCE_URL"

# ============================================================================
# OUTPUT FILES
# ============================================================================

# Preprocessed data output
PREPROCESSED_DATA_PATH: Final[Path] = DATA_PROCESSED_DIR / "preprocessed_data.parquet"

# Cross-validation report
CV_REPORT_PATH: Final[Path] = DATA_PROCESSED_DIR / "cv_report.json"

# Cycle-specific coefficients (fallback model offsets)
CYCLE_COEFFICIENTS_PATH: Final[Path] = DATA_PROCESSED_DIR / "cycle_specific_coefficients.json"

# Sensitivity report
SENSITIVITY_REPORT_PATH: Final[Path] = DATA_PROCESSED_DIR / "sensitivity_report.json"

# Reconstruction output for pre-satellite era
RECONSTRUCTION_1610_2002_PATH: Final[Path] = DATA_PROCESSED_DIR / "reconstruction_1610_2002.parquet"

# Variance analysis output
VARIANCE_ANALYSIS_PATH: Final[Path] = DATA_PROCESSED_DIR / "variance_analysis.json"

# Final comparison report
FINAL_REPORT_PATH: Final[Path] = DATA_PROCESSED_DIR / "final_report.md"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def ensure_directories() -> None:
    """
    Ensure all required project directories exist.
    Creates them if they don't exist.
    
    This function is called during project initialization to set up
    the directory structure for data, models, and analysis outputs.
    """
    directories = [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        CODE_MODELS_DIR,
        CODE_ANALYSIS_DIR,
        CODE_DATA_DIR,
        CODE_MODELS_ARTIFACTS_DIR,
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory exists: {directory}")

def get_gap_filling_strategy(gap_days: int) -> str:
    """
    Determine the gap filling strategy based on gap duration.
    
    Args:
        gap_days: Duration of the gap in days
        
    Returns:
        Strategy name: 'linear_interpolation' for gaps < 1 year,
                      'tsi_proxy' for gaps >= 1 year
    """
    if gap_days < GAP_THRESHOLD_DAYS:
        return "linear_interpolation"
    else:
        return "tsi_proxy"

def get_tsi_proxy_value() -> float:
    """
    Get the TSI proxy value for large gaps (FR-002).
    
    Returns:
        The TSI proxy value in W/m²
    """
    return TSI_PROXY_VALUE

def get_sensitivity_thresholds() -> List[float]:
    """
    Get the list of sensitivity analysis thresholds (FR-009).
    
    Returns:
        List of threshold values to sweep
    """
    return SENSITIVITY_THRESHOLDS

def validate_paths() -> bool:
    """
    Validate that all required paths exist and are accessible.
    
    Returns:
        True if all paths are valid, False otherwise
    """
    required_paths = [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        CODE_MODELS_DIR,
        CODE_ANALYSIS_DIR,
        CODE_DATA_DIR,
    ]
    
    all_valid = True
    for path in required_paths:
        if not path.exists():
            logger.warning(f"Path does not exist: {path}")
            all_valid = False
        elif not os.access(path, os.W_OK):
            logger.warning(f"Path is not writable: {path}")
            all_valid = False
    
    return all_valid

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    logger.info("Running config module validation...")
    
    # Ensure directories exist
    ensure_directories()
    
    # Validate paths
    if validate_paths():
        logger.info("All paths validated successfully.")
    else:
        logger.warning("Some paths are missing or not accessible.")
    
    # Print configuration summary
    logger.info(f"Project Root: {PROJECT_ROOT}")
    logger.info(f"Random Seed: {RANDOM_SEED}")
    logger.info(f"Gap Threshold: {GAP_THRESHOLD_DAYS} days")
    logger.info(f"TSI Proxy Value: {TSI_PROXY_VALUE} W/m²")
    logger.info(f"Sensitivity Thresholds: {SENSITIVITY_THRESHOLDS}")
    logger.info(f"Bootstrap Iterations: {BOOTSTRAP_ITERATIONS}")
    
    print("Configuration module loaded successfully.")