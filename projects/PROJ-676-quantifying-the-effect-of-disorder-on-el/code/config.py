"""
Configuration module for the project.
Defines hyperparameters, random seeds, and path constants.
"""
import os
from pathlib import Path
from typing import Dict, Any


class Config:
    """
    Central configuration class for the project.
    """
    def __init__(self):
        # Project root
        self.PROJECT_ROOT = Path(__file__).parent.parent
        
        # Directories
        self.CODE_DIR = self.PROJECT_ROOT / 'code'
        self.DATA_DIR = self.PROJECT_ROOT / 'data'
        self.RAW_DIR = self.DATA_DIR / 'raw'
        self.PROCESSED_DIR = self.DATA_DIR / 'processed'
        self.METADATA_DIR = self.DATA_DIR / 'metadata'
        self.FIGURES_DIR = self.PROJECT_ROOT / 'figures'
        self.DOCS_DIR = self.PROJECT_ROOT / 'docs'
        self.SPECS_DIR = self.PROJECT_ROOT / 'specs'
        
        # Ensure directories exist
        for d in [self.RAW_DIR, self.PROCESSED_DIR, self.METADATA_DIR, self.FIGURES_DIR, self.DOCS_DIR]:
            d.mkdir(parents=True, exist_ok=True)
        
        # Hyperparameters
        self.DEFAULT_SEED = 42
        self.NUM_REALIZATIONS = 100
        self.LIST_DEFAULT = [100, 200, 400, 800, 1600]
        self.W_LIST_DEFAULT = [0.5, 1.0, 2.0]
        
        # Numerical tolerances
        self.EIGENVALUE_TOL = 1e-6
        self.CONVERGENCE_TOL = 1e-5
        
        # Memory limits (in GB)
        self.RAM_LIMIT_GB = 6.0
        
        # Output paths
        self.RESIDUALS_FILE = self.METADATA_DIR / 'residuals.json'
        self.SCALING_FITS_FILE = self.PROCESSED_DIR / 'scaling_fits.json'
        self.LYAPUNOV_FILE = self.PROCESSED_DIR / 'lyapunov_exponents.json'
        self.PROVENANCE_FILE = self.METADATA_DIR / 'provenance.json'


_config_instance = None


def get_config() -> Config:
    """
    Singleton factory for Config.
    
    Returns:
        Config: The global configuration instance.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance