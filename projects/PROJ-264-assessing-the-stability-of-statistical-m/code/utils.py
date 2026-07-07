"""
Utility functions for the llmXive stability assessment pipeline.

Provides:
- Seed pinning for reproducibility
- Logging setup with file and console handlers
- Error handling wrappers for robust execution
"""
import logging
import os
import random
import sys
import traceback
from functools import wraps
from typing import Any, Callable, Optional

import numpy as np

# --- Seed Pinning ---

def set_seed(seed: int = 42) -> None:
    """
    Pin random seeds for reproducibility across numpy, random, and torch (if available).
    
    Args:
        seed: The integer seed value to use.
    """
    random.seed(seed)
    np.random.seed(seed)
    # Attempt to set torch seed if available, ignore if not
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass  # Torch not required, ignore

# --- Logging Setup ---

def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    project_root: Optional[str] = None
) -> logging.Logger:
    """
    Configure logging for the project.
    
    Args:
        log_level: The logging level (e.g., logging.INFO).
        log_file: Optional path to a log file. If None, only console logging is used.
        project_root: Optional root directory for the project. Used to resolve relative log paths.
    
    Returns:
        A configured logger instance.
    """
    logger = logging.getLogger("llmXive")
    logger.setLevel(log_level)
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler
    if log_file:
        if project_root:
            # Resolve relative to project root if provided
            full_log_path = os.path.join(project_root, log_file)
            # Ensure directory exists
            os.makedirs(os.path.dirname(full_log_path), exist_ok=True)
        else:
            full_log_path = log_file
            
        file_handler = logging.FileHandler(full_log_path)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# --- Error Handling Wrappers ---

class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass

def log_and_reraise(
    logger: Optional[logging.Logger] = None,
    message: Optional[str] = None
) -> Callable:
    """
    Decorator to wrap a function, logging errors with stack trace before re-raising.
    
    Args:
        logger: Optional logger instance. If None, uses 'llmXive'.
        message: Optional custom error message prefix.
    
    Returns:
        Decorated function.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            log = logger or logging.getLogger("llmXive")
            try:
                return func(*args, **kwargs)
            except Exception as e:
                err_msg = f"Error in {func.__name__}: {str(e)}"
                if message:
                    err_msg = f"{message} - {err_msg}"
                
                log.critical(err_msg)
                log.critical(traceback.format_exc())
                raise
        return wrapper
    return decorator

def safe_execute(
    func: Callable,
    default: Any = None,
    logger: Optional[logging.Logger] = None,
    error_type: type = Exception
) -> Callable:
    """
    Decorator to execute a function safely, catching specific errors and returning a default.
    
    Args:
        func: The function to wrap.
        default: The value to return if an error occurs.
        logger: Optional logger instance.
        error_type: The type of exception to catch (default: Exception).
    
    Returns:
        Decorated function.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        log = logger or logging.getLogger("llmXive")
        try:
            return func(*args, **kwargs)
        except error_type as e:
            log.warning(f"Caught {error_type.__name__} in {func.__name__}: {e}")
            return default
        except Exception as e:
            # Re-raise unexpected errors
            log.error(f"Unexpected error in {func.__name__}: {e}")
            raise
    return wrapper