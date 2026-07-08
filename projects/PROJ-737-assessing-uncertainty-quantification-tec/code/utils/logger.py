"""
Logging infrastructure for the UQ pipeline.
Configures a hierarchical logger that captures convergence failures,
memory overflows, and general pipeline progress.
"""
import logging
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Ensure the utils directory is treated as a package if run directly
if __name__ == "__main__" and __package__ is None:
    __package__ = "code.utils"
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Project root for log file placement
PROJECT_ROOT = Path(__file__).parent.parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "pipeline.log"

# Log format with timestamp, level, module, and message
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Custom levels for specific pipeline events (optional but useful)
# We stick to standard levels for compatibility, but use specific messages for detection
CONVERGENCE_ERROR = "CONVERGENCE_FAIL"
MEMORY_OVERFLOW = "MEMORY_OOM"

_logger_instance: Optional[logging.Logger] = None


def setup_logger(
    name: str = "uq_pipeline",
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = True,
) -> logging.Logger:
    """
    Configures and returns a logger instance for the pipeline.
    
    Args:
        name: Logger name (namespace).
        level: Minimum log level.
        log_to_file: Whether to write to logs/pipeline.log.
        log_to_console: Whether to print to stdout.
    
    Returns:
        Configured logging.Logger instance.
    """
    global _logger_instance
    
    if _logger_instance and _logger_instance.name == name:
        return _logger_instance

    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        logger.handlers.clear()

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    if log_to_file:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    _logger_instance = logger
    return logger


def get_logger(name: str = "uq_pipeline") -> logging.Logger:
    """
    Retrieves or creates a logger with the given name.
    Ensures the root pipeline logger is initialized first.
    """
    if _logger_instance is None:
        setup_logger()
    return logging.getLogger(name)


def log_convergence_failure(
    logger: logging.Logger,
    method_name: str,
    dataset_name: str,
    error_details: str,
    iteration_count: Optional[int] = None,
) -> None:
    """
    Logs a structured convergence failure event.
    
    Args:
        logger: Logger instance.
        method_name: Name of the UQ method (e.g., 'GPR', 'MC_Dropout').
        dataset_name: Name of the dataset.
        error_details: Specific error message or traceback snippet.
        iteration_count: Number of iterations run before failure.
    """
    msg = (
        f"CONVERGENCE_FAIL: Method={method_name}, Dataset={dataset_name}, "
        f"Iterations={iteration_count}, Error={error_details}"
    )
    logger.error(msg)


def log_memory_overflow(
    logger: logging.Logger,
    component: str,
    current_usage_gb: float,
    threshold_gb: float,
) -> None:
    """
    Logs a structured memory overflow event.
    
    Args:
        logger: Logger instance.
        component: Name of the component causing overflow.
        current_usage_gb: Current RAM usage in GB.
        threshold_gb: The configured threshold that was exceeded.
    """
    msg = (
        f"MEMORY_OOM: Component={component}, "
        f"Current_Usage_GB={current_usage_gb:.2f}, "
        f"Threshold_GB={threshold_gb:.2f}"
    )
    logger.critical(msg)


def log_pipeline_start() -> None:
    """Logs the start of the main pipeline execution."""
    logger = get_logger()
    logger.info("=" * 60)
    logger.info("Pipeline execution started.")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info("=" * 60)


def log_pipeline_end(success: bool = True) -> None:
    """Logs the end of the main pipeline execution."""
    logger = get_logger()
    status = "SUCCESS" if success else "PARTIAL FAILURE (see errors above)"
    logger.info("=" * 60)
    logger.info(f"Pipeline execution finished with status: {status}")
    logger.info("=" * 60)


# Convenience function to get the main pipeline logger immediately
# This allows other modules to import and use `logger` directly if needed
# but encourages passing the logger instance for better testability.
main_logger = setup_logger()


if __name__ == "__main__":
    # Basic self-test of the logger
    test_logger = setup_logger("test_logger")
    test_logger.info("Logger infrastructure initialized successfully.")
    test_logger.warning("This is a warning message.")
    log_convergence_failure(
        test_logger, 
        "TestMethod", 
        "TestDataset", 
        "Simulated divergence after 10 steps"
    )
    log_memory_overflow(
        test_logger, 
        "DataLoader", 
        2.1, 
        1.8
    )
    print(f"Logs written to: {LOG_FILE}")
