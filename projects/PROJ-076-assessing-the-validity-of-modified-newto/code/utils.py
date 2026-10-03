"""
Utility functions for the project.
"""
import os
import logging
import random
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Optional

# Global logger instance to be initialized by setup_logging
_logger: Optional[logging.Logger] = None

def setup_logging(log_level: int = logging.INFO, log_file: Optional[str] = 'pipeline.log') -> logging.Logger:
    """
    Configure the root logger for the pipeline.
    
    Sets up a logger that outputs to both console and a file.
    This function should be called once at the start of the pipeline.
    
    Args:
        log_level: The logging level (e.g., logging.INFO, logging.DEBUG).
        log_file: Path to the log file. If None, file handler is not added.
        
    Returns:
        The configured root logger instance.
    """
    global _logger
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup handlers
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)
    
    # File handler (optional)
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)
        except Exception as e:
            # Fallback to console only if file creation fails
            print(f"Warning: Could not create log file '{log_file}': {e}")
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers to avoid duplicates
    root_logger.handlers = []
    
    for handler in handlers:
        root_logger.addHandler(handler)
    
    _logger = root_logger
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module or component.
    
    Args:
        name: Name of the logger (usually __name__ of the module).
        
    Returns:
        A logger instance. If setup_logging hasn't been called, 
        it will configure a basic logger first.
    """
    global _logger
    if _logger is None:
        # Auto-initialize if not set up yet
        setup_logging()
    return logging.getLogger(name)

def log_stage(stage_name: str, logger: Optional[logging.Logger] = None, status: str = "Starting"):
    """
    Log the start or end of a pipeline stage.
    
    Args:
        stage_name: Name of the pipeline stage (e.g., "Data Download", "Model Fitting").
        logger: Logger instance. If None, uses the default logger.
        status: Either "Starting" or "Completed".
    """
    if logger is None:
        logger = get_logger(__name__)
    
    if status == "Starting":
        logger.info(f"--- Starting {stage_name} ---")
    elif status == "Completed":
        logger.info(f"--- Completed {stage_name} ---")
    else:
        logger.info(f"--- {status}: {stage_name} ---")

def set_global_seed(seed: int):
    """
    Set global random seeds for reproducibility.
    
    This ensures deterministic behavior across:
    - Python's built-in random module
    - NumPy's random number generator
    - Python's hash randomization (via environment variable)
    
    Args:
        seed: Integer seed value for reproducibility.
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_timestamp() -> str:
    """Get current timestamp string."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero."""
    if denominator == 0:
        return default
    return numerator / denominator

def format_number(value: float, precision: int = 4) -> str:
    """Format a number with fixed precision."""
    return f"{value:.{precision}f}"

def ensure_directory(path: Path):
    """Ensure a directory exists."""
    path.mkdir(parents=True, exist_ok=True)

def calculate_chi2(observed: np.ndarray, predicted: np.ndarray, errors: np.ndarray) -> float:
    """Calculate Chi-squared statistic."""
    if len(observed) != len(predicted) or len(observed) != len(errors):
        raise ValueError("Arrays must be of equal length")
    return float(np.sum(((observed - predicted) / errors) ** 2))

def calculate_aic(n: int, k: int, chi2: float) -> float:
    """Calculate Akaike Information Criterion."""
    return 2 * k + chi2

def calculate_bic(n: int, k: int, chi2: float) -> float:
    """Calculate Bayesian Information Criterion."""
    return np.log(n) * k + chi2
