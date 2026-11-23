import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

_logger_instance = None
_logger_initialized = False

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent

def ensure_log_directory() -> Path:
    """Ensure the logs directory exists."""
    project_root = get_project_root()
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    return logs_dir

def setup_logger(name: str = "pipeline", level: int = logging.INFO) -> logging.Logger:
    """Set up the pipeline logger."""
    global _logger_instance, _logger_initialized

    if _logger_initialized:
        return _logger_instance

    logs_dir = ensure_log_directory()
    log_file = logs_dir / f"{name}.log"

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers.clear()

    # Create file handler
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(level)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    _logger_instance = logger
    _logger_initialized = True

    return logger

def get_pipeline_logger() -> logging.Logger:
    """Get the pipeline logger instance."""
    global _logger_instance, _logger_initialized

    if not _logger_initialized:
        return setup_logger()

    return _logger_instance

def log_info(message: str, logger: Optional[logging.Logger] = None):
    """Log an info message."""
    if logger is None:
        logger = get_pipeline_logger()
    logger.info(message)

def log_warning(message: str, logger: Optional[logging.Logger] = None):
    """Log a warning message."""
    if logger is None:
        logger = get_pipeline_logger()
    logger.warning(message)

def log_error(message: str, logger: Optional[logging.Logger] = None):
    """Log an error message."""
    if logger is None:
        logger = get_pipeline_logger()
    logger.error(message)

def log_abort(message: str, logger: Optional[logging.Logger] = None):
    """Log an abort message and raise an exception."""
    if logger is None:
        logger = get_pipeline_logger()
    logger.critical(f"ABORT: {message}")
    raise RuntimeError(f"Pipeline aborted: {message}")

def log_exclusion(row_id: str, reason: str, step: str, logger: Optional[logging.Logger] = None):
    """Log an exclusion event."""
    if logger is None:
        logger = get_pipeline_logger()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"{row_id},{reason},step={step},timestamp={timestamp}"
    logs_dir = ensure_log_directory()
    exclusion_file = logs_dir / f"{step}_exclusions.log"
    with open(exclusion_file, 'a', encoding='utf-8') as f:
        f.write(message + '\n')
    logger.info(f"Excluded row {row_id}: {reason}")

def log_exclusion_count(total_rows: int, excluded_rows: int, step: str, logger: Optional[logging.Logger] = None):
    """Log the exclusion count summary."""
    if logger is None:
        logger = get_pipeline_logger()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"SUMMARY,step={step},total_rows={total_rows},excluded_rows={excluded_rows},timestamp={timestamp}"
    logs_dir = ensure_log_directory()
    exclusion_file = logs_dir / f"{step}_exclusions.log"
    with open(exclusion_file, 'a', encoding='utf-8') as f:
        f.write(message + '\n')
    logger.info(f"Exclusion summary for {step}: {excluded_rows}/{total_rows} rows excluded")

def check_log_file_exists(log_name: str = "pipeline.log") -> bool:
    """Check if a log file exists."""
    logs_dir = ensure_log_directory()
    log_file = logs_dir / log_name
    return log_file.exists()

def read_log_file(log_name: str = "pipeline.log") -> str:
    """Read the contents of a log file."""
    logs_dir = ensure_log_directory()
    log_file = logs_dir / log_name
    if not log_file.exists():
        raise FileNotFoundError(f"Log file {log_file} does not exist.")
    return log_file.read_text(encoding='utf-8')
