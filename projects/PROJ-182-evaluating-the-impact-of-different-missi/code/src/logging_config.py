"""
Logging infrastructure configuration for the RD simulation pipeline.

This module sets up a centralized logging system to track simulation progress,
estimator execution, and errors across all components. It ensures consistent
log formatting and file output for reproducibility and debugging.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Constants
LOG_DIR = Path("results")
LOG_FILE_NAME = "simulation.log"
DEFAULT_LOG_LEVEL = logging.INFO
SIMULATION_LOG_LEVEL = logging.DEBUG

# Global logger instance
_logger: Optional[logging.Logger] = None


def setup_logging(
    log_level: int = DEFAULT_LOG_LEVEL,
    log_dir: Optional[Path] = None,
    log_file: Optional[str] = None,
    enable_console: bool = True,
    enable_file: bool = True
) -> logging.Logger:
    """
    Configure and return the project logger.

    This function sets up a logger with handlers for both console and file output.
    It creates the log directory if it doesn't exist and configures the logging
    format to include timestamp, level, module, and message.

    Args:
        log_level: Minimum logging level (e.g., logging.DEBUG, logging.INFO)
        log_dir: Directory path for log files. Defaults to LOG_DIR constant.
        log_file: Name of the log file. Defaults to LOG_FILE_NAME constant.
        enable_console: Whether to add a console handler.
        enable_file: Whether to add a file handler.

    Returns:
        The configured logger instance.

    Example:
        >>> logger = setup_logging()
        >>> logger.info("Simulation started")
    """
    global _logger

    # Avoid re-configuring if already set up
    if _logger is not None:
        return _logger

    # Resolve paths
    log_directory = log_dir or LOG_DIR
    log_filename = log_file or LOG_FILE_NAME
    log_path = log_directory / log_filename

    # Create log directory if it doesn't exist
    log_directory.mkdir(parents=True, exist_ok=True)

    # Create logger
    _logger = logging.getLogger("rd_simulation")
    _logger.setLevel(log_level)

    # Clear any existing handlers to avoid duplicates
    _logger.handlers.clear()

    # Define log format
    log_format = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(log_format)
        _logger.addHandler(console_handler)

    # File handler
    if enable_file:
        file_handler = logging.FileHandler(log_path, mode='a', encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(log_format)
        _logger.addHandler(file_handler)

    # Add a special handler for simulation-specific detailed logs if needed
    # This could be useful for debugging specific simulation runs
    if log_level <= SIMULATION_LOG_LEVEL:
        # Log simulation details to a separate file if debug level is requested
        sim_log_path = log_directory / "simulation_debug.log"
        sim_handler = logging.FileHandler(sim_log_path, mode='a', encoding='utf-8')
        sim_handler.setLevel(SIMULATION_LOG_LEVEL)
        sim_handler.setFormatter(log_format)
        _logger.addHandler(sim_handler)

    _logger.info("Logging infrastructure initialized successfully.")
    _logger.debug(f"Log directory: {log_directory}")
    _logger.debug(f"Log file: {log_path}")

    return _logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance, creating the root logger if necessary.

    Args:
        name: Optional name for a child logger. If None, returns the root logger.

    Returns:
        A logger instance.

    Example:
        >>> logger = get_logger("estimators")
        >>> logger.info("Starting estimation")
    """
    if _logger is None:
        # Auto-setup if logger hasn't been explicitly configured
        setup_logging()

    if name is None:
        return _logger
    return _logger.getChild(name)


def log_simulation_start(config: dict) -> None:
    """
    Log the start of a simulation run with configuration details.

    Args:
        config: Dictionary containing simulation configuration parameters.
    """
    logger = get_logger("simulation")
    logger.info("=" * 80)
    logger.info("SIMULATION START")
    logger.info("=" * 80)
    logger.debug(f"Configuration: {config}")


def log_simulation_end(duration: float, status: str = "SUCCESS") -> None:
    """
    Log the end of a simulation run.

    Args:
        duration: Time taken for the simulation in seconds.
        status: Status of the simulation (e.g., "SUCCESS", "FAILED", "PARTIAL").
    """
    logger = get_logger("simulation")
    logger.info("=" * 80)
    logger.info(f"SIMULATION END - Status: {status} - Duration: {duration:.2f}s")
    logger.info("=" * 80)


def log_missingness_generation(mechanism: str, rate: float, n_samples: int) -> None:
    """
    Log the generation of a missingness pattern.

    Args:
        mechanism: Type of missingness (MCAR, MAR, MNAR).
        rate: Missingness rate (0.0 to 1.0).
        n_samples: Number of samples processed.
    """
    logger = get_logger("missingness")
    logger.info(f"Generated {mechanism} missingness: rate={rate:.2f}, n={n_samples}")


def log_estimator_run(estimator_name: str, config: dict, status: str = "COMPLETED") -> None:
    """
    Log the execution of an estimator.

    Args:
        estimator_name: Name of the estimator.
        config: Estimator configuration parameters.
        status: Execution status (e.g., "COMPLETED", "FAILED", "CONVERGENCE_ISSUE").
    """
    logger = get_logger("estimators")
    logger.info(f"Running estimator: {estimator_name} - Status: {status}")
    logger.debug(f"Estimator config: {config}")
    if status == "FAILED":
        logger.error(f"Estimator {estimator_name} failed to complete.")


def log_error(context: str, error: Exception, level: int = logging.ERROR) -> None:
    """
    Log an error with context information.

    Args:
        context: Description of where the error occurred.
        error: The exception object.
        level: Logging level for the error.
    """
    logger = get_logger("errors")
    logger.log(level, f"Error in {context}: {str(error)}")
    logger.debug("Traceback:", exc_info=True)


# Initialize logger with default settings if this module is imported directly
if __name__ == "__main__":
    logger = setup_logging()
    logger.info("Logging module initialized and tested.")
    logger.debug("All logging handlers configured.")