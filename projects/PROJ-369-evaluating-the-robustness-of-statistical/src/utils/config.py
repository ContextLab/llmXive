"""
Configuration management for the statistical robustness evaluation pipeline.

Handles random seed management, global constants, and environment-based
configuration for reproducible research.
"""
import os
import random
from pathlib import Path
from typing import Optional, Dict, Any, Union
import numpy as np
import logging

# Get logger for this module
logger = logging.getLogger(__name__)

# ============================================================================
# Project Root and Directory Constants
# ============================================================================

# Determine project root (assumes code/ is at root, src/ is inside code/)
# This handles both direct execution and execution from different working directories
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_CODE_ROOT = _PROJECT_ROOT / "code"
_DATA_ROOT = _PROJECT_ROOT / "data"
_DATA_RAW = _DATA_ROOT / "raw"
_DATA_PROCESSED = _DATA_ROOT / "processed"
_DATA_RESULTS = _DATA_ROOT / "results"
_FIGURES_ROOT = _PROJECT_ROOT / "figures"
_SPEC_ROOT = _PROJECT_ROOT / "specs"

# Ensure directories exist
_DATA_ROOT.mkdir(parents=True, exist_ok=True)
_DATA_RAW.mkdir(parents=True, exist_ok=True)
_DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
_DATA_RESULTS.mkdir(parents=True, exist_ok=True)
_FIGURES_ROOT.mkdir(parents=True, exist_ok=True)

# ============================================================================
# Random Seed Management
# ============================================================================

# Default seed for reproducibility
DEFAULT_SEED = 42

# Current active seed (can be changed at runtime)
_active_seed: Optional[int] = None

# Lock for thread-safe seed setting (for future parallel extensions)
_seed_lock = None  # Initialized on first use if needed

def set_seed(seed: Optional[int] = None) -> int:
    """
    Set the random seed for all random number generators.
    
    Args:
        seed: Seed value. If None, uses DEFAULT_SEED.
    
    Returns:
        The seed value that was set.
    
    Side effects:
        Sets seeds for Python's random, numpy.random, and logs the action.
    """
    global _active_seed
    _active_seed = seed if seed is not None else DEFAULT_SEED
    
    # Set seed for Python's random module
    random.seed(_active_seed)
    
    # Set seed for numpy
    np.random.seed(_active_seed)
    
    logger.info(f"Random seed set to: {_active_seed}")
    
    return _active_seed

def get_seed() -> int:
    """
    Get the currently active random seed.
    
    Returns:
        The active seed, or DEFAULT_SEED if not yet set.
    """
    return _active_seed if _active_seed is not None else DEFAULT_SEED

def reset_seed() -> int:
    """
    Reset the random seed to the default value.
    
    Returns:
        The default seed value.
    """
    return set_seed(DEFAULT_SEED)

# Initialize seed on module load for reproducibility
set_seed(DEFAULT_SEED)

# ============================================================================
# Statistical Constants and Thresholds
# ============================================================================

# Significance level for hypothesis testing
ALPHA_LEVEL = 0.05

# ADF test stationarity threshold (p-value)
ADF_STATIONARITY_THRESHOLD = 0.05

# Minimum series length for meaningful analysis
MIN_SERIES_LENGTH = 25

# Maximum lag for ACF computation
MAX_ACF_LAG = 20

# Hurst exponent bounds
HURST_MIN = 0.0
HURST_MAX = 1.0

# Synthetic data generation parameters
SYNTHETIC_H_VALUES = [0.5, 0.7, 0.8, 0.9]
SYNTHETIC_MEAN_TARGET = 0.0
SYNTHETIC_MEAN_TOLERANCE = 0.01
SYNTHETIC_H_TOLERANCE = 0.05

# Series length categories
SERIES_LENGTH_SMALL = 500
SERIES_LENGTH_MEDIUM = 2000
SERIES_LENGTH_LARGE = 10000

# ============================================================================
# Data Processing Parameters
# ============================================================================

# Maximum number of differences to apply before giving up
MAX_DIFFERENCING_ITERATIONS = 5

# Linear interpolation tolerance for missing values
MAX_MISSING_GAP_SIZE = 10

# Resampling frequency target (for consistency)
TARGET_RESAMPLE_FREQ = 'H'  # Hourly

# ============================================================================
# Monte Carlo and Simulation Parameters
# ============================================================================

# Number of trials for Monte Carlo simulations
MONTE_CARLO_TRIALS = 10000  # Default, can be overridden per experiment

# Number of permutations for null distribution
NULL_PERMUTATIONS = 1000

# ============================================================================
# Environment-Based Configuration
# ============================================================================

def get_config_from_env() -> Dict[str, Any]:
    """
    Load configuration overrides from environment variables.
    
    Returns:
        Dictionary of configuration overrides.
    """
    config = {}
    
    # Check for environment variable overrides
    if 'RANDOM_SEED' in os.environ:
        try:
            config['seed'] = int(os.environ['RANDOM_SEED'])
        except ValueError:
            logger.warning(f"Invalid RANDOM_SEED value: {os.environ['RANDOM_SEED']}")
    
    if 'ALPHA_LEVEL' in os.environ:
        try:
            config['alpha_level'] = float(os.environ['ALPHA_LEVEL'])
        except ValueError:
            logger.warning(f"Invalid ALPHA_LEVEL value: {os.environ['ALPHA_LEVEL']}")
    
    if 'MONTE_CARLO_TRIALS' in os.environ:
        try:
            config['monte_carlo_trials'] = int(os.environ['MONTE_CARLO_TRIALS'])
        except ValueError:
            logger.warning(f"Invalid MONTE_CARLO_TRIALS value: {os.environ['MONTE_CARLO_TRIALS']}")
    
    if 'DATA_ROOT' in os.environ:
        config['data_root'] = Path(os.environ['DATA_ROOT'])
    
    return config

def apply_env_config() -> None:
    """
    Apply configuration overrides from environment variables.
    """
    env_config = get_config_from_env()
    
    if 'seed' in env_config:
        set_seed(env_config['seed'])
    
    if 'alpha_level' in env_config:
      globals()['ALPHA_LEVEL'] = env_config['alpha_level']
    
    if 'monte_carlo_trials' in env_config:
      globals()['MONTE_CARLO_TRIALS'] = env_config['monte_carlo_trials']
    
    if 'data_root' in env_config:
      globals()['_DATA_ROOT'] = env_config['data_root']
      # Update derived paths
      globals()['_DATA_RAW'] = _DATA_ROOT / "raw"
      globals()['_DATA_PROCESSED'] = _DATA_ROOT / "processed"
      globals()['_DATA_RESULTS'] = _DATA_ROOT / "results"
      
      # Ensure directories exist
      _DATA_ROOT.mkdir(parents=True, exist_ok=True)
      _DATA_RAW.mkdir(parents=True, exist_ok=True)
      _DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
      _DATA_RESULTS.mkdir(parents=True, exist_ok=True)
    
    if env_config:
        logger.info(f"Applied environment configuration: {list(env_config.keys())}")

# Apply environment config on module load
apply_env_config()

# ============================================================================
# Path Accessors
# ============================================================================

def get_data_raw_path() -> Path:
    """Get the path to the raw data directory."""
    return _DATA_RAW

def get_data_processed_path() -> Path:
    """Get the path to the processed data directory."""
    return _DATA_PROCESSED

def get_data_results_path() -> Path:
    """Get the path to the results directory."""
    return _DATA_RESULTS

def get_figures_path() -> Path:
    """Get the path to the figures directory."""
    return _FIGURES_ROOT

def get_project_root() -> Path:
    """Get the project root directory."""
    return _PROJECT_ROOT

def get_code_root() -> Path:
    """Get the code root directory."""
    return _CODE_ROOT

# ============================================================================
# Validation Helpers
# ============================================================================

def validate_series_length(n: int) -> bool:
    """
    Check if a series length is sufficient for analysis.
    
    Args:
        n: Series length.
    
    Returns:
        True if n >= MIN_SERIES_LENGTH, False otherwise.
    """
    return n >= MIN_SERIES_LENGTH

def validate_hurst_exponent(h: float) -> bool:
    """
    Check if a Hurst exponent value is within valid bounds.
    
    Args:
        h: Hurst exponent value.
    
    Returns:
        True if 0.0 <= h <= 1.0, False otherwise.
    """
    return HURST_MIN <= h <= HURST_MAX

def validate_p_value(p: float) -> bool:
    """
    Check if a p-value is within valid bounds.
    
    Args:
        p: P-value.
    
    Returns:
        True if 0.0 <= p <= 1.0, False otherwise.
    """
    return 0.0 <= p <= 1.0

# ============================================================================
# Module Information
# ============================================================================

__version__ = "0.1.0"
__author__ = "llmXive Pipeline"

def get_version_info() -> Dict[str, Any]:
    """
    Get version and configuration information.
    
    Returns:
        Dictionary with version and key configuration values.
    """
    return {
        "version": __version__,
        "author": __author__,
        "seed": get_seed(),
        "alpha_level": ALPHA_LEVEL,
        "min_series_length": MIN_SERIES_LENGTH,
        "max_acf_lag": MAX_ACF_LAG,
        "data_root": str(_DATA_ROOT),
        "figures_root": str(_FIGURES_ROOT),
    }