import os
import logging
import random
import numpy as np
from pathlib import Path
from datetime import datetime
import sys

# Add parent directory to path to allow relative imports if running as script
sys.path.insert(0, str(Path(__file__).parent))

# Global seed state
_global_seed = None

def setup_logging(log_level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """
    Setup logging infrastructure.
    """
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance by name.
    """
    return logging.getLogger(name)

def log_stage(logger: logging.Logger, stage: str, message: str) -> None:
    """
    Log a stage message with a standard format.
    """
    logger.info(f"[{stage}] {message}")

def set_global_seed(seed: int) -> None:
    """
    Set the global random seed for reproducibility.
    """
    global _global_seed
    _global_seed = seed
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_timestamp() -> str:
    """
    Get the current timestamp in ISO format.
    """
    return datetime.now().isoformat()

def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if b is zero.
    """
    if b == 0:
        return default
    return a / b

def format_number(value: float, precision: int = 4) -> str:
    """
    Format a number with specified precision.
    """
    return f"{value:.{precision}f}"

def ensure_directory(path: Path) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    """
    path.mkdir(parents=True, exist_ok=True)

def calculate_chi2(observed: np.ndarray, predicted: np.ndarray, errors: np.ndarray) -> float:
    """
    Calculate Chi-squared statistic.
    """
    return np.sum(((observed - predicted) / errors) ** 2)

def calculate_aic(n: int, k: int, chi2: float) -> float:
    """
    Calculate Akaike Information Criterion.
    """
    return chi2 + 2 * k

def calculate_bic(n: int, k: int, chi2: float) -> float:
    """
    Calculate Bayesian Information Criterion.
    """
    return chi2 + k * np.log(n)

# Optional imports to prevent errors if not used
from typing import Optional

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = get_logger("utils_test")
    log_stage(logger, "TEST", "Utils module loaded successfully")