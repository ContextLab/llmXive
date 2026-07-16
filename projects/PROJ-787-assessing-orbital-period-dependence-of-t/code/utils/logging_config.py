import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any

# Constants for log formatting and paths
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LOG_DIR = "logs"
DEFAULT_LOG_FILE = "pipeline.log"
MAX_LOG_BYTES = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5

# Global logger registry to prevent re-initialization issues
_loggers: Dict[str, logging.Logger] = {}
_initialized = False

def _ensure_log_dir(log_dir: Optional[Path] = None) -> Path:
    """Ensure the log directory exists."""
    if log_dir is None:
        log_dir = Path(DEFAULT_LOG_DIR)
    
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)
    
    return log_dir

def setup_logging(
    level: int = logging.INFO,
    log_dir: Optional[Path] = None,
    log_file: Optional[str] = None,
    console_output: bool = True,
    force: bool = False
) -> logging.Logger:
    """
    Configure the root logger with file and console handlers.
    
    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG)
        log_dir: Directory for log files. Defaults to DEFAULT_LOG_DIR.
        log_file: Name of the log file. Defaults to DEFAULT_LOG_FILE.
        console_output: Whether to add a console handler.
        force: If True, reconfigure existing handlers.
    
    Returns:
        The configured root logger.
    """
    global _initialized
    
    log_dir = _ensure_log_dir(log_dir)
    log_file_path = log_dir / (log_file or DEFAULT_LOG_FILE)
    
    root_logger = logging.getLogger()
    
    if force or not _initialized:
        # Clear existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        root_logger.setLevel(level)
    
    # Add file handler if not already present or if forced
    if force or not any(isinstance(h, RotatingFileHandler) for h in root_logger.handlers):
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=MAX_LOG_BYTES,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Add console handler if requested
    if console_output:
        if force or not any(isinstance(h, logging.StreamHandler) and h.stream == sys.stdout for h in root_logger.handlers):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
    
    _initialized = True
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance by name.
    
    Args:
        name: Logger name (usually __name__ of the module).
    
    Returns:
        A configured logger instance.
    """
    if name not in _loggers:
        logger = logging.getLogger(name)
        _loggers[name] = logger
    return _loggers[name]

def configure_module_logger(
    module_name: str,
    level: int = logging.INFO,
    log_dir: Optional[Path] = None
) -> logging.Logger:
    """
    Configure a specific module's logger.
    
    Args:
        module_name: Name of the module to configure.
        level: Logging level.
        log_dir: Directory for log files.
    
    Returns:
        The configured logger.
    """
    logger = get_logger(module_name)
    logger.setLevel(level)
    
    # Ensure the root logger is set up first
    if not logging.getLogger().handlers:
        setup_logging(level=level, log_dir=log_dir)
    
    return logger

def get_module_logger(module_path: str) -> logging.Logger:
    """
    Get a logger for a specific module path (e.g., 'code.ingest.download_dr25').
    
    Args:
        module_path: The module path string.
    
    Returns:
        A configured logger.
    """
    return configure_module_logger(module_path)

def log_ingestion_summary(
    logger: logging.Logger,
    total_records: int,
    filtered_records: int,
    excluded_reasons: Optional[Dict[str, int]] = None,
    duplicates_removed: int = 0
) -> None:
    """
    Log a structured summary of an ingestion or preprocessing step.
    
    Args:
        logger: The logger instance to use.
        total_records: Total number of input records.
        filtered_records: Number of records passing filters.
        excluded_reasons: Dictionary of exclusion reasons and counts.
        duplicates_removed: Number of duplicate records removed.
    """
    logger.info("=" * 60)
    logger.info("INGESTION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total input records: {total_records}")
    logger.info(f"Records passing filters: {filtered_records}")
    
    if excluded_reasons:
        logger.info("Exclusion breakdown:")
        for reason, count in excluded_reasons.items():
            logger.info(f"  - {reason}: {count}")
    
    if duplicates_removed > 0:
        logger.info(f"Duplicates removed: {duplicates_removed}")
    
    logger.info("=" * 60)
