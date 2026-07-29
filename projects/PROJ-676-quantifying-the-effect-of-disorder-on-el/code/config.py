"""
Configuration constants for the disorder analysis project.
"""
import os
from pathlib import Path
from typing import Dict, Any

class Config:
    """Project configuration."""
    
    # Project root
    PROJECT_ROOT = Path(__file__).parent.parent
    
    # Data paths
    RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw"
    PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed"
    METADATA_PATH = PROJECT_ROOT / "data" / "metadata"
    FIGURES_PATH = PROJECT_ROOT / "figures"
    
    # Ensure directories exist
    RAW_DATA_PATH.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_PATH.mkdir(parents=True, exist_ok=True)
    METADATA_PATH.mkdir(parents=True, exist_ok=True)
    FIGURES_PATH.mkdir(parents=True, exist_ok=True)
    
    # Residuals log path (for T017)
    RESIDUALS_PATH = METADATA_PATH / "residuals.json"
    
    # Analysis output paths
    SCALING_FITS_PATH = PROCESSED_DATA_PATH / "scaling_fits.json"
    LYAPUNOV_EXPONENTS_PATH = PROCESSED_DATA_PATH / "lyapunov_exponents.json"
    BONFERRONI_RESULTS_PATH = PROCESSED_DATA_PATH / "bonferroni_results.json"
    METHOD_AGREEMENT_PATH = PROCESSED_DATA_PATH / "method_agreement_report.json"
    FIT_RESULTS_PATH = PROCESSED_DATA_PATH / "fit_results.json"
    
    # Visualization paths
    VISUALIZATIONS_DIR = PROCESSED_DATA_PATH / "visualizations"
    VISUALIZATIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Hyperparameters
    L_LIST = [100, 200, 400, 800, 1600]
    W_LIST = [0.5, 1.0, 2.0]
    NUM_REALIZATIONS = 100
    SEED = 42
    
    # Analysis parameters
    ENERGY_WINDOW = 0.1  # Energy range around E=0 for PR calculation
    MIN_L_FOR_TM = 400  # Minimum system size for TM validation
    AGREEMENT_THRESHOLD = 0.10  # 10% agreement threshold for TM vs PR
    MIN_AGREEMENT_FRACTION = 0.80  # 80% of realizations must agree
    
    # Memory limits
    MAX_RAM_GB = 6.0  # Switch to sparse if exceeded
    
def get_config() -> Config:
    """
    Get the global configuration instance.
    
    Returns:
        Config instance.
    """
    return Config()
