"""
llmXive PROJ-076: Utility functions for logging, seeding, and common operations.
"""
import os
import logging
import random
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Optional, Union

# --- Logging Setup (T008 implementation) ---

_logger_instance: Optional[logging.Logger] = None

def setup_logging(log_level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """
    Initialize the project logger.
    
    Args:
        log_level: Logging level (e.g., logging.INFO).
        log_file: Optional path to log file. If None, logs to console only.
    
    Returns:
        Configured logger instance.
    """
    global _logger_instance
    if _logger_instance is not None:
        return _logger_instance
    
    logger = logging.getLogger("llmXive_PROJ076")
    logger.setLevel(log_level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # File handler if specified
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(log_level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    _logger_instance = logger
    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get the project logger or a child logger.
    """
    if _logger_instance is None:
        setup_logging()
    if name:
        return _logger_instance.getChild(name)
    return _logger_instance

def log_stage(stage_name: str, message: str, level: int = logging.INFO):
    """
    Log a message with a stage prefix.
    """
    logger = get_logger()
    logger.log(level, f"[{stage_name}] {message}")

# --- Deterministic Seed Utility (T006 implementation) ---

def set_global_seed(seed: int = 42) -> None:
    """
    Pin the random seed for reproducibility across Python, NumPy, and related libraries.
    
    This ensures deterministic behavior for any randomized operations in the pipeline,
    crucial for reproducible scientific research.
    
    Args:
        seed: Integer seed value. Default is 42.
    """
    random.seed(seed)
    np.random.seed(seed)
    # If torch or tensorflow are used later, add their seeders here
    # os.environ['PYTHONHASHSEED'] = str(seed)
    log_stage("SEED", f"Global seed set to {seed}")

# --- Common Utilities ---

def get_timestamp() -> str:
    """
    Get current timestamp in ISO format.
    """
    return datetime.now().isoformat(timespec='seconds')

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if denominator is zero.
    """
    if denominator == 0:
        return default
    return numerator / denominator

def format_number(value: float, precision: int = 4, scientific: bool = False) -> str:
    """
    Format a number with specified precision.
    """
    if scientific:
        return f"{value:.{precision}e}"
    return f"{value:.{precision}f}"

def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p

# --- Statistical Metrics (Required for T024, defined here to avoid circular imports) ---

def calculate_chi2(observed: np.ndarray, predicted: np.ndarray, uncertainty: np.ndarray) -> float:
    """
    Calculate reduced chi-squared statistic.
    """
    if len(observed) != len(predicted) or len(observed) != len(uncertainty):
        raise ValueError("Arrays must have the same length")
    
    if np.any(uncertainty == 0):
        raise ValueError("Uncertainty cannot be zero")
    
    residuals = observed - predicted
    chi2 = np.sum((residuals / uncertainty) ** 2)
    dof = len(observed) - 1  # Assuming 1 fitted parameter for simplicity, adjust as needed
    
    if dof <= 0:
        return float('inf')
    
    return chi2 / dof

def calculate_aic(chi2: float, k: int, n: int) -> float:
    """
    Calculate Akaike Information Criterion (AIC).
    
    Args:
        chi2: Chi-squared statistic.
        k: Number of parameters.
        n: Number of data points.
    """
    return n * np.log(chi2 / n) + 2 * k

def calculate_bic(chi2: float, k: int, n: int) -> float:
    """
    Calculate Bayesian Information Criterion (BIC).
    
    Args:
        chi2: Chi-squared statistic.
        k: Number of parameters.
        n: Number of data points.
    """
    return n * np.log(chi2 / n) + k * np.log(n)