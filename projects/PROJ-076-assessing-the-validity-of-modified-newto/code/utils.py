"""
Utility functions for the MOND validity assessment pipeline.

Includes:
- Random seed management for reproducibility
- Logging infrastructure
- Common helper functions
"""

import os
import logging
import random
import numpy as np
from pathlib import Path
from datetime import datetime

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Global logger instance (initialized lazily or explicitly)
_logger = None

def setup_logging(log_level=logging.INFO, log_file=None):
    """
    Set up logging infrastructure for the pipeline.
    
    This function configures a named logger 'mond_pipeline' with handlers
    for both console and optional file output. It also updates the global
    logger instance used throughout the pipeline.
    
    Args:
        log_level: Logging level (default: INFO)
        log_file: Optional path to log file. If None, logs to console only.
                
    Returns:
        logging.Logger: Configured logger instance
    """
    global _logger
    
    # Create logger
    _logger = logging.getLogger('mond_pipeline')
    _logger.setLevel(log_level)
    
    # Clear existing handlers to prevent duplicates on re-calls
    _logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    _logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(log_level)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        _logger.addHandler(file_handler)
    
    return _logger

def get_logger():
    """
    Retrieve the global pipeline logger.
    
    If logging has not been initialized yet, this returns a default
    console-only logger at INFO level.
    
    Returns:
        logging.Logger: The configured logger instance
    """
    global _logger
    if _logger is None:
        _logger = logging.getLogger('mond_pipeline')
        if not _logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            _logger.addHandler(handler)
            _logger.setLevel(logging.INFO)
    return _logger

def log_stage(stage_name, message=""):
    """
    Log a pipeline stage transition.
    
    This utility provides a standardized way to mark significant points
    in the pipeline execution (e.g., 'Data Download Started', 'Fitting Complete').
    
    Args:
        stage_name: Name of the pipeline stage
        message: Optional additional context message
    """
    logger = get_logger()
    if message:
        logger.info(f"[STAGE: {stage_name}] {message}")
    else:
        logger.info(f"[STAGE: {stage_name}]")

# Initialize logger immediately for module-level usage
# This ensures that if 'from utils import logger' is used, it works
# though explicit setup_logging() is preferred for configuration.
try:
    _logger = setup_logging()
except Exception:
    # Fallback if logging setup fails (e.g., in restricted environments)
    _logger = logging.getLogger('mond_pipeline')
    _logger.setLevel(logging.INFO)
    if not _logger.handlers:
        _logger.addHandler(logging.StreamHandler())

def set_global_seed(seed=42):
    """
    Set global random seeds for reproducibility.
    
    This function pins the random seed for Python's built-in `random` module,
    NumPy's random number generator, and sets the environment variable
    `PYTHONHASHSEED` to ensure deterministic behavior across runs.
    
    Args:
        seed: Integer seed value (default: 42)
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    _logger.info(f"Global random seed set to {seed}")

def get_timestamp():
    """
    Get current timestamp in ISO format.
    
    Returns:
        str: ISO formatted timestamp string
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def safe_divide(numerator, denominator, default=0.0):
    """
    Safe division that handles zero denominators.
    
    Args:
        numerator: Numerator value
        denominator: Denominator value
        default: Default value to return if division by zero (default: 0.0)
                
    Returns:
        float: Result of division or default value
    """
    if denominator == 0:
        return default
    return numerator / denominator

def format_number(value, precision=4):
    """
    Format a number with specified precision.
    
    Args:
        value: Number to format
        precision: Number of decimal places (default: 4)
                
    Returns:
        str: Formatted number string
    """
    if isinstance(value, (int, float)):
        if abs(value) < 1e-6:
            return f"{value:.2e}"
        return f"{value:.{precision}f}"
    return str(value)

def ensure_directory(path):
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Path to directory
                
    Returns:
        Path: The directory path
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def calculate_chi2(observed, predicted, uncertainties):
    """
    Calculate chi-squared statistic.
    
    Args:
        observed: Observed values
        predicted: Predicted values
        uncertainties: Uncertainties in observed values
                
    Returns:
        float: Chi-squared value
    """
    observed = np.array(observed)
    predicted = np.array(predicted)
    uncertainties = np.array(uncertainties)
    
    residuals = observed - predicted
    chi2 = np.sum((residuals / uncertainties) ** 2)
    return chi2

def calculate_aic(chi2, n_params, n_points):
    """
    Calculate Akaike Information Criterion.
    
    Args:
        chi2: Chi-squared value
        n_params: Number of model parameters
        n_points: Number of data points
                
    Returns:
        float: AIC value
    """
    return chi2 + 2 * n_params

def calculate_bic(chi2, n_params, n_points):
    """
    Calculate Bayesian Information Criterion.
    
    Args:
        chi2: Chi-squared value
        n_params: Number of model parameters
        n_points: Number of data points
                
    Returns:
        float: BIC value
    """
    return chi2 + n_params * np.log(n_points)
