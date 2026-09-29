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

def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """Configure the root logger."""
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('pipeline.log')
        ]
    )
    return logging.getLogger()

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)

def log_stage(stage_name: str, logger: Optional[logging.Logger] = None):
    """Log the start/end of a pipeline stage."""
    if logger is None:
        logger = logging.getLogger()
    logger.info(f"--- Starting {stage_name} ---")

def set_global_seed(seed: int):
    """Set global random seeds for reproducibility."""
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
