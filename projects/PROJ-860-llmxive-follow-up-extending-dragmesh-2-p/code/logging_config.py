"""
Logging configuration for the llmXive Virtual Tactile Zero-Shot Adaptation pipeline.

This module sets up centralized logging configuration to ensure consistent
formatting, file paths, and log levels across all project scripts.

FR-005 Compliance: Logging includes specific fields for reproducibility tracking
including object_id, policy_type, and k_est values.
"""

import os
import sys
import logging
import logging.handlers
from pathlib import Path
from typing import Optional

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent

# Log directories
LOG_DIR = PROJECT_ROOT / "state" / "logs"
TRAIN_LOG_FILE = LOG_DIR / "training.log"
EVAL_LOG_FILE = LOG_DIR / "evaluation.log"
AGGREGATE_LOG_FILE = LOG_DIR / "aggregation.log"
ANALYSIS_LOG_FILE = LOG_DIR / "analysis.log"

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Log format with timestamp, level, module, and message
# Includes specific fields for FR-005 reproducibility
LOG_FORMAT = (
    "%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - "
    "%(message)s"
)

# Detailed format for debugging (includes thread and process info)
DEBUG_LOG_FORMAT = (
    "%(asctime)s - %(levelname)s - %(name)s - %(threadName)s - "
    "%(processName)s - %(filename)s:%(lineno)d - %(funcName)s - "
    "%(message)s"
)

# Date format for timestamps
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Default log level
DEFAULT_LEVEL = logging.INFO

# Console formatter
console_formatter = logging.Formatter(
    fmt=LOG_FORMAT,
    datefmt=DATE_FORMAT
)

# File formatter (same as console for consistency)
file_formatter = logging.Formatter(
    fmt=LOG_FORMAT,
    datefmt=DATE_FORMAT
)

def get_logger(
    name: str,
    level: int = DEFAULT_LEVEL,
    log_file: Optional[Path] = None,
    propagate: bool = False
) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        level: Logging level (default: INFO)
        log_file: Optional file path for log output
        propagate: Whether to propagate to parent loggers (default: False)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = propagate
    
    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        # Ensure parent directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Use RotatingFileHandler to prevent unbounded growth
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

def setup_training_logger(level: int = DEFAULT_LEVEL) -> logging.Logger:
    """
    Setup logger for training pipeline.
    
    Logs training-specific events including:
    - Episode start/end
    - Reward weight adjustments
    - k_est estimates
    - Policy updates
    
    Args:
        level: Logging level
    
    Returns:
        Configured training logger
    """
    return get_logger(
        name="training",
        level=level,
        log_file=TRAIN_LOG_FILE
    )

def setup_evaluation_logger(level: int = DEFAULT_LEVEL) -> logging.Logger:
    """
    Setup logger for evaluation pipeline.
    
    Logs evaluation-specific events including:
    - Object loading
    - Policy execution (adaptive vs static)
    - Success/failure outcomes
    - Object_id and policy_type for pairing
    
    Args:
        level: Logging level
    
    Returns:
        Configured evaluation logger
    """
    return get_logger(
        name="evaluation",
        level=level,
        log_file=EVAL_LOG_FILE
    )

def setup_aggregation_logger(level: int = DEFAULT_LEVEL) -> logging.Logger:
    """
    Setup logger for data aggregation pipeline.
    
    Logs aggregation events including:
    - Log file discovery
    - Record parsing
    - CSV writing
    
    Args:
        level: Logging level
    
    Returns:
        Configured aggregation logger
    """
    return get_logger(
        name="aggregation",
        level=level,
        log_file=AGGREGATE_LOG_FILE
    )

def setup_analysis_logger(level: int = DEFAULT_LEVEL) -> logging.Logger:
    """
    Setup logger for statistical analysis pipeline.
    
    Logs analysis events including:
    - Data loading
    - Statistical test results
    - Threshold verification
    
    Args:
        level: Logging level
    
    Returns:
        Configured analysis logger
    """
    return get_logger(
        name="analysis",
        level=level,
        log_file=ANALYSIS_LOG_FILE
    )

def setup_all_loggers(level: int = DEFAULT_LEVEL) -> dict:
    """
    Setup all project loggers at once.
    
    Args:
        level: Logging level for all loggers
    
    Returns:
        Dictionary mapping logger names to logger instances
    """
    return {
        "training": setup_training_logger(level),
        "evaluation": setup_evaluation_logger(level),
        "aggregation": setup_aggregation_logger(level),
        "analysis": setup_analysis_logger(level)
    }

# Convenience function for quick setup
def init_logging(level: int = DEFAULT_LEVEL) -> None:
    """
    Initialize logging for the entire project.
    
    This should be called at the entry point of each script to ensure
    consistent logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    setup_all_loggers(level)
    
    # Log initialization
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(console_formatter)
        root_logger.addHandler(handler)

if __name__ == "__main__":
    # Test logging configuration
    init_logging(logging.DEBUG)
    
    logger = setup_training_logger()
    logger.info("Logging configuration test successful")
    logger.debug("Debug message from training logger")
    logger.warning("Warning message from training logger")
    
    eval_logger = setup_evaluation_logger()
    eval_logger.info("Evaluation logger initialized")
    
    print(f"\nLog files created in: {LOG_DIR}")
    print(f"Training log: {TRAIN_LOG_FILE}")
    print(f"Evaluation log: {EVAL_LOG_FILE}")
    print(f"Aggregation log: {AGGREGATE_LOG_FILE}")
    print(f"Analysis log: {ANALYSIS_LOG_FILE}")