"""
llmXive Statistical Sensitivity Analysis Package.

This package provides tools for assessing the sensitivity of common
statistical tests (t-test, ANOVA, Chi-squared, Fisher's Exact) to
dataset size and distributional properties.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

# Configure basic logging for the package
def _get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Get or create a logger for the llmXive package.
    
    Args:
        name: Logger name (default: "llmXive")
        
    Returns:
        Configured logging.Logger instance
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

# Initialize the package logger
logger = _get_logger()

# Export the logger for use by other modules
__all__ = ["logger"]

def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> None:
    """
    Configure logging for the entire package with optional file output.
    
    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
        log_file: Optional path to a log file. If provided, logs are written
                 to both console and file.
    """
    # Update root logger level
    logging.getLogger("llmXive").setLevel(level)
    
    # Add file handler if specified
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        logging.getLogger("llmXive").addHandler(file_handler)

# Convenience function to get a module-specific logger
def get_module_logger(module_name: str) -> logging.Logger:
    """
    Get a logger for a specific module within the package.
    
    Args:
        module_name: Name of the module (e.g., "data_generator")
        
    Returns:
        Logger instance with name "llmXive.<module_name>"
    """
    return _get_logger(f"llmXive.{module_name}")