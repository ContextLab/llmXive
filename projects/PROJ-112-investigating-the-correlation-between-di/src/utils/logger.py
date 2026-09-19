import logging
import os
from pathlib import Path
from typing import Optional
import sys

# Cache for logger instances
_LOGGER_CACHE = {}
_LOG_DIR = "logs"
_LOG_FILE = "pipeline.log"

def get_logger(name: str, log_dir: Optional[str] = None, log_file: Optional[str] = None) -> logging.Logger:
    """
    Get or create a logger with the specified name and configuration.
    
    Args:
        name: Name of the logger.
        log_dir: Directory for log files. Defaults to 'logs' in project root.
        log_file: Log file name. Defaults to 'pipeline.log'.
    
    Returns:
        Configured Logger instance.
    """
    if name in _LOGGER_CACHE:
        return _LOGGER_CACHE[name]
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Prevent adding handlers multiple times if called repeatedly
    if logger.handlers:
        _LOGGER_CACHE[name] = logger
        return logger
    
    # Determine paths
    if log_dir is None:
        # Try to find project root or use current working directory
        project_root = Path.cwd()
        log_dir = project_root / _LOG_DIR
    else:
        log_dir = Path(log_dir)
    
    log_dir.mkdir(parents=True, exist_ok=True)
    
    if log_file is None:
        log_file = _LOG_FILE
    
    log_path = log_dir / log_file
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File handler for all logs
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Console handler for important logs
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    
    # Special handler for MaAsLin2/R output (simulated via specific log levels)
    # We use a custom format for warnings and errors that might come from R
    r_output_formatter = logging.Formatter(
        '[R/MaAsLin2] %(asctime)s - %(levelname)s - %(message)s'
    )
    r_handler = logging.FileHandler(log_dir / "r_output.log")
    r_handler.setLevel(logging.WARNING)
    r_handler.setFormatter(r_output_formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.addHandler(r_handler)
    
    _LOGGER_CACHE[name] = logger
    return logger

def reset_logger_cache():
    """
    Reset the logger cache. Useful for testing.
    """
    global _LOGGER_CACHE
    for name, logger in _LOGGER_CACHE.items():
        # Remove all handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()
    _LOGGER_CACHE = {}

# Convenience function for MaAsLin2 specific logging
def log_maaslin2_status(logger: logging.Logger, message: str, level: str = "INFO"):
    """
    Log a MaAsLin2 status message with appropriate formatting.
    """
    if level == "WARNING":
        logger.warning(f"[MaAsLin2 Status] {message}")
    elif level == "ERROR":
        logger.error(f"[MaAsLin2 Status] {message}")
    else:
        logger.info(f"[MaAsLin2 Status] {message}")

def log_convergence_warning(logger: logging.Logger, message: str):
    """
    Log a convergence warning from R/MaAsLin2.
    """
    logger.warning(f"[Convergence Warning] {message}")

def log_r_output(logger: logging.Logger, message: str):
    """
    Log raw output from R package execution.
    """
    logger.warning(f"[R Output] {message}")
