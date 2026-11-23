"""
Configuration management for the Cosmic Ray Anisotropy Solar-Cycle Modulation project.
"""
import os
import logging
from typing import Optional


# Default configuration values
DEFAULT_BIN_SIZE_DAYS: int = 27
MIN_BIN_SIZE_DAYS: int = 14
MAX_BIN_SIZE_DAYS: int = 365
HEALPIX_NSIDE: int = 64
BONFERRONI_ALPHA: float = 0.0017  # 0.05 / 30 tests approx
LOMB_SCARGLE_MIN_PERIOD: float = 10.0  # days
LOMB_SCARGLE_MAX_PERIOD: float = 3650.0  # days (10 years)

# Data paths relative to project root
DATA_RAW_DIR: str = "data/raw"
DATA_PROCESSED_DIR: str = "data/processed"
DATA_RESULTS_DIR: str = "data/results"
FIGURES_DIR: str = "figures"
REPORTS_DIR: str = "reports"

# Retry configuration
MAX_RETRIES: int = 3
RETRY_BACKOFF_FACTOR: float = 2.0
REQUEST_TIMEOUT: int = 30

# Logging configuration
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Configure and return a logger with standard formatting.
    
    Args:
        name: Logger name.
        
    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
        
    logger.setLevel(getattr(logging, LOG_LEVEL.upper()))
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)
    
    logger.addHandler(handler)
    return logger


def validate_bin_size(bin_size_days: int) -> bool:
    """
    Validate that the bin size is within acceptable bounds.
    
    Args:
        bin_size_days: Bin size in days to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    return MIN_BIN_SIZE_DAYS <= bin_size_days <= MAX_BIN_SIZE_DAYS


def get_config_summary(bin_size_days: Optional[int] = None) -> Dict[str, Any]:
    """
    Get a summary of the current configuration.
    
    Args:
        bin_size_days: Optional override for bin size.
        
    Returns:
        Dictionary containing configuration summary.
    """
    effective_bin = bin_size_days if bin_size_days is not None else DEFAULT_BIN_SIZE_DAYS
    return {
        'bin_size_days': effective_bin,
        'healpix_nside': HEALPIX_NSIDE,
        'bonferroni_alpha': BONFERRONI_ALPHA,
        'max_retries': MAX_RETRIES,
        'log_level': LOG_LEVEL,
        'data_dirs': {
            'raw': DATA_RAW_DIR,
            'processed': DATA_PROCESSED_DIR,
            'results': DATA_RESULTS_DIR
        }
    }
