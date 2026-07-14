import logging
import sys
import os
from typing import Optional
from datetime import datetime

# Global logger instance for the simulation pipeline
_logger: Optional[logging.Logger] = None

def get_logger(name: str = "llmXive.simulation") -> logging.Logger:
    """
    Returns a configured logger instance for the simulation pipeline.
    Ensures a single, consistent configuration across all modules.
    """
    global _logger
    if _logger is None:
        _logger = logging.getLogger(name)
        if _logger.handlers:
            # Already configured
            return _logger

        _logger.setLevel(logging.DEBUG)

        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # Create formatter
        formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)

        # Add handler to logger
        _logger.addHandler(console_handler)

        # Prevent propagation to root if not desired, but usually good to keep
        # _logger.propagate = False

    return _logger

def setup_file_logging(output_dir: str = "data/logs") -> logging.Logger:
    """
    Configures file logging for the simulation run.
    Creates a log file named with the current timestamp.
    """
    global _logger
    if _logger is None:
        _logger = get_logger()

    # Ensure directory exists
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(output_dir, f"simulation_{timestamp}.log")

    # Check if file handler already exists to avoid duplicates
    has_file_handler = any(
        isinstance(h, logging.FileHandler) for h in _logger.handlers
    )

    if not has_file_handler:
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        _logger.addHandler(file_handler)

    return _logger

def log_simulation_start(
    sample_size: int,
    effect_size: float,
    test_type: str,
    alpha: float,
    iterations: int,
    seed: int
) -> None:
    """Logs the start of a specific simulation condition."""
    logger = get_logger()
    logger.info(
        f"Starting simulation: n={sample_size}, effect={effect_size}, "
        f"test={test_type}, alpha={alpha}, iterations={iterations}, seed={seed}"
    )

def log_simulation_end(
    sample_size: int,
    test_type: str,
    type_i_errors: int,
    type_ii_errors: int,
    total_iterations: int
) -> None:
    """Logs the summary of a simulation condition."""
    logger = get_logger()
    logger.info(
        f"Completed simulation: n={sample_size}, test={test_type}. "
        f"Type I: {type_i_errors}/{total_iterations}, Type II: {type_ii_errors}/{total_iterations}"
    )

def log_data_generation(
    distribution: str,
    params: dict,
    n_samples: int,
    seed: int
) -> None:
    """Logs details about data generation."""
    logger = get_logger()
    logger.debug(
        f"Generating {distribution} data: n={n_samples}, params={params}, seed={seed}"
    )

def log_test_execution(
    test_name: str,
    statistic: float,
    p_value: float,
    details: Optional[str] = None
) -> None:
    """Logs the result of a statistical test execution."""
    logger = get_logger()
    msg = f"Test {test_name}: stat={statistic:.4f}, p={p_value:.4f}"
    if details:
        msg += f" | {details}"
    logger.debug(msg)

def log_fallback_trigger(
    original_test: str,
    fallback_test: str,
    reason: str
) -> None:
    """Logs when a statistical test falls back to an alternative."""
    logger = get_logger()
    logger.warning(
        f"Fallback triggered: {original_test} -> {fallback_test}. Reason: {reason}"
    )

def log_validation_step(
    dataset_name: str,
    step: str,
    status: str,
    details: Optional[str] = None
) -> None:
    """Logs validation steps for real data processing."""
    logger = get_logger()
    msg = f"Validation [{dataset_name}]: {step} -> {status}"
    if details:
        msg += f" | {details}"
    logger.info(msg)

def log_error(message: str, exception: Optional[Exception] = None) -> None:
    """Logs an error with optional exception details."""
    logger = get_logger()
    if exception:
        logger.error(f"{message}: {exception}", exc_info=True)
    else:
        logger.error(message)

def log_warning(message: str) -> None:
    """Logs a warning."""
    get_logger().warning(message)

def log_debug(message: str) -> None:
    """Logs a debug message."""
    get_logger().debug(message)
