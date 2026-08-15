import os
import sys
import logging
from datetime import datetime
from pathlib import Path

from config import get_path_env_override


# Global registry to hold configured logger instances
_loggers = {}
_handlers_configured = False


def ensure_directories(log_dir: Path) -> None:
    """Ensure the logging directory exists."""
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)


def setup_logging(log_dir: Path) -> None:
    """
    Configure the root logging infrastructure.
    
    Sets up file handlers for specific log categories (data quality, model diagnostics)
    and ensures the directory structure exists.
    
    Args:
        log_dir: The directory where log files will be written.
    """
    global _handlers_configured
    if _handlers_configured:
        return

    ensure_directories(log_dir)

    # Define log file paths
    data_quality_log_path = log_dir / "data_quality.log"
    model_diagnostics_log_path = log_dir / "model_diagnostics.log"
    general_log_path = log_dir / "pipeline.log"

    # Configure root logger to NOT propagate to avoid duplicate console output
    # if other parts of the system configure root differently, though usually
    # we want a file handler on the root for general pipeline events.
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Remove any existing handlers to ensure idempotency in testing
    if root_logger.handlers:
        root_logger.handlers.clear()

    # General Pipeline Handler (INFO and above)
    general_handler = logging.FileHandler(general_log_path, mode='a', encoding='utf-8')
    general_handler.setLevel(logging.INFO)
    general_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    general_handler.setFormatter(general_formatter)
    root_logger.addHandler(general_handler)

    # Data Quality Handler (DEBUG and above)
    dq_handler = logging.FileHandler(data_quality_log_path, mode='a', encoding='utf-8')
    dq_handler.setLevel(logging.DEBUG)
    dq_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    dq_handler.setFormatter(dq_formatter)
    
    # Create a specific logger for data quality
    data_quality_logger = logging.getLogger('data_quality')
    data_quality_logger.addHandler(dq_handler)
    data_quality_logger.setLevel(logging.DEBUG)
    data_quality_logger.propagate = False  # Don't double-log to root

    # Model Diagnostics Handler (DEBUG and above)
    md_handler = logging.FileHandler(model_diagnostics_log_path, mode='a', encoding='utf-8')
    md_handler.setLevel(logging.DEBUG)
    md_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    md_handler.setFormatter(md_formatter)

    # Create a specific logger for model diagnostics
    model_diagnostics_logger = logging.getLogger('model_diagnostics')
    model_diagnostics_logger.addHandler(md_handler)
    model_diagnostics_logger.setLevel(logging.DEBUG)
    model_diagnostics_logger.propagate = False

    # Console handler for immediate feedback during development (WARNING and above)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    _handlers_configured = True
    # Log initialization
    root_logger.info(f"Logging infrastructure initialized. Logs written to {log_dir}")


def get_data_quality_logger() -> logging.Logger:
    """
    Retrieve the dedicated logger for data quality checks.
    
    Returns:
        A logger instance configured to write to data_quality.log.
    """
    log_dir = Path(get_path_env_override("RESULTS_LOGS_DIR", "results/logs"))
    setup_logging(log_dir)
    logger = logging.getLogger('data_quality')
    if not logger.hasHandlers():
        # Fallback if setup_logging wasn't called explicitly first
        setup_logging(log_dir)
    return logger


def get_model_diagnostics_logger() -> logging.Logger:
    """
    Retrieve the dedicated logger for model diagnostics.
    
    Returns:
        A logger instance configured to write to model_diagnostics.log.
    """
    log_dir = Path(get_path_env_override("RESULTS_LOGS_DIR", "results/logs"))
    setup_logging(log_dir)
    logger = logging.getLogger('model_diagnostics')
    if not logger.hasHandlers():
        setup_logging(log_dir)
    return logger


def main() -> None:
    """
    Entry point to verify logging setup and write a sample log entry.
    """
    log_dir = Path(get_path_env_override("RESULTS_LOGS_DIR", "results/logs"))
    setup_logging(log_dir)

    dq_logger = get_data_quality_logger()
    md_logger = get_model_diagnostics_logger()
    root_logger = logging.getLogger()

    # Write test entries to verify the infrastructure
    dq_logger.info("Data Quality Logger initialized successfully.")
    dq_logger.debug("Sample data quality check: Schema validation passed.")
    
    md_logger.info("Model Diagnostics Logger initialized successfully.")
    md_logger.debug("Sample model diagnostic: Convergence check started.")
    
    root_logger.info("Pipeline logging system operational.")

    print(f"Logging infrastructure setup complete. Check {log_dir} for log files.")


if __name__ == "__main__":
    main()
