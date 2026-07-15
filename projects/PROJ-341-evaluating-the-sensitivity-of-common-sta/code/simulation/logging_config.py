import logging
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any
import json

LOG_FILE_PATH = "data/simulation/simulation.log"
_logger_instance = None

def setup_logging():
    """Configure logging for the simulation."""
    global _logger_instance
    if _logger_instance is not None:
        return _logger_instance

    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler
    file_handler = logging.FileHandler(LOG_FILE_PATH)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    _logger_instance = logging.getLogger(__name__)
    return _logger_instance

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    if _logger_instance is None:
        setup_logging()
    return logging.getLogger(name)

def log_simulation_params(logger: logging.Logger, params: Dict[str, Any]):
    """Log simulation parameters."""
    logger.info(f"Simulation Parameters: {json.dumps(params, indent=2)}")

def log_seed_usage(logger: logging.Logger, seed: int, context: str):
    """Log usage of a specific seed."""
    logger.debug(f"Seed {seed} used for: {context}")

def log_iteration_status(logger: logging.Logger, current: int, total: int, status: str):
    """Log iteration progress."""
    if current % 100 == 0 or current == total:
        logger.info(f"Iteration {current}/{total}: {status}")

def log_test_result(logger: logging.Logger, test_type: str, n: int, effect_size: float, p_value: float, decision: str):
    """Log result of a single test."""
    logger.debug(f"Test: {test_type}, n={n}, es={effect_size}, p={p_value:.4f}, {decision}")

def log_warning_assumption_violated(logger: logging.Logger, test_type: str, assumption: str):
    """Log assumption violation warning."""
    logger.warning(f"Assumption violated in {test_type}: {assumption}")

def log_fallback_triggered(logger: logging.Logger, test_type: str, fallback_type: str):
    """Log fallback trigger."""
    logger.info(f"Fallback triggered for {test_type}: {fallback_type}")

def log_output_file_written(logger: logging.Logger, filepath: str):
    """Log that an output file was written."""
    logger.info(f"Output file written: {filepath}")

def log_error_details(logger: logging.Logger, error: Exception, context: str):
    """Log error details."""
    logger.error(f"Error in {context}: {str(error)}", exc_info=True)

def log_shutdown(logger: logging.Logger):
    """Log shutdown message."""
    logger.info("Simulation shutdown complete.")

def get_log_file_path() -> str:
    """Return the path to the log file."""
    return LOG_FILE_PATH
