"""
Logging configuration and utilities for the plant defense allocation pipeline.

Provides a centralized logging setup that writes to both console and files
with consistent formatting and log levels.
"""
import logging
import sys
from pathlib import Path
from typing import Optional
import os

from .config import get_config, get_data_path


# Singleton pattern to ensure single logger configuration
_logger: Optional[logging.Logger] = None
_configured: bool = False


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get or create the project logger.
    
    Args:
        name: Optional name for the logger. If None, uses the project root name.
    
    Returns:
        Configured logging.Logger instance.
    """
    global _logger, _configured
    
    if not _configured:
        setup_logging()
    
    if name is None:
        if _logger is None:
            _logger = logging.getLogger("plant_defense_pipeline")
        return _logger
    
    return logging.getLogger(f"plant_defense_pipeline.{name}")


def setup_logging(
    level: int = logging.INFO,
    log_dir: Optional[Path] = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Configure the root logger for the project.
    
    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        log_dir: Directory for log files. Defaults to data/logs from config.
        log_file: Specific log filename. Defaults to pipeline.log.
    
    Returns:
        The configured root logger.
    """
    global _logger, _configured
    
    if _configured:
        return _logger
    
    # Get configuration
    config = get_config()
    if log_dir is None:
        data_path = get_data_path()
        log_dir = data_path / "logs"
    
    # Ensure log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)
    
    if log_file is None:
        log_file = "pipeline.log"
    
    log_path = log_dir / log_file
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Create handlers
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    
    file_handler = logging.FileHandler(log_path, mode='a')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    
    # Configure root logger
    root_logger = logging.getLogger("plant_defense_pipeline")
    root_logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Also configure the standard 'logging' module root
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[console_handler, file_handler]
    )
    
    _logger = root_logger
    _configured = True
    
    _logger.info("Logging system initialized. Log file: %s", log_path)
    
    return _logger


def set_log_level(level: int) -> None:
    """
    Update the log level for all handlers.
    
    Args:
        level: New logging level.
    """
    logger = get_logger()
    logger.setLevel(level)
    
    for handler in logger.handlers:
        handler.setLevel(level)


class PipelineLogger:
    """
    Context-aware logger wrapper for pipeline stages.
    
    Provides methods to log stage entry/exit and progress.
    """
    
    def __init__(self, stage_name: str):
        """
        Initialize the stage logger.
        
        Args:
            stage_name: Name of the current pipeline stage.
        """
        self.stage_name = stage_name
        self.logger = get_logger(stage_name)
    
    def start(self, message: str = "") -> None:
        """Log the start of a stage."""
        self.logger.info("=== START: %s === %s", self.stage_name, message)
    
    def progress(self, message: str) -> None:
        """Log a progress update."""
        self.logger.info("[%s] %s", self.stage_name, message)
    
    def complete(self, message: str = "") -> None:
        """Log the completion of a stage."""
        self.logger.info("=== COMPLETE: %s === %s", self.stage_name, message)
    
    def error(self, message: str) -> None:
        """Log an error."""
        self.logger.error("[%s] ERROR: %s", self.stage_name, message)
    
    def warning(self, message: str) -> None:
        """Log a warning."""
        self.logger.warning("[%s] WARNING: %s", self.stage_name, message)
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.complete()
        else:
            self.error(f"Failed with exception: {exc_val}")
        return False  # Don't suppress exceptions
