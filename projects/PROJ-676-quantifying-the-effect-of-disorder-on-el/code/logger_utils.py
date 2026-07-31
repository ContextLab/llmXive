import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from code.logger import get_logger, NumericalLogger
from code.config import get_config

def get_logger_instance(output_path: Optional[Path] = None) -> NumericalLogger:
    """
    Get a NumericalLogger instance for logging residuals.
    
    Args:
        output_path: Optional path for the output file.
        
    Returns:
        A NumericalLogger instance.
    """
    return get_logger(output_path)

def log_eigenvalue_residual(norm: float, flag: bool, task: str = "eigh",
                           L: Optional[int] = None, W: Optional[float] = None,
                           realization_index: Optional[int] = None):
    """
    Log an eigenvalue residual.
    
    Args:
        norm: Residual norm.
        flag: Convergence flag.
        task: Task name.
        L: System size.
        W: Disorder strength.
        realization_index: Realization index.
    """
    logger = get_logger_instance()
    logger.log_residual(norm, flag, task, L, W, realization_index)

def log_numerical_warning(message: str):
    """Log a numerical warning."""
    logging.warning(f"NUMERICAL WARNING: {message}")

def log_numerical_error(message: str):
    """Log a numerical error."""
    logging.error(f"NUMERICAL ERROR: {message}")
