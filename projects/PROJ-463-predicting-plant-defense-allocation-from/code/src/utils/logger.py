"""
Logging and provenance tracking utilities for the plant defense allocation pipeline.
Implements a centralized logging configuration with file and console handlers,
and integrates with the provenance system to record pipeline execution details.
"""
import logging
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import json

from .config import get_config


class PipelineLogger:
    """
    A centralized logger wrapper that ensures consistent log formatting,
    file rotation, and integration with the project's configuration.
    """
    _instance: Optional['PipelineLogger'] = None
    _logger: Optional[logging.Logger] = None
    _setup_complete: bool = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, log_level: str = "INFO", log_dir: Optional[Path] = None):
        if self._setup_complete:
            return
        
        self.log_level = log_level
        self.log_dir = log_dir or get_config().log_dir
        
        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create main logger
        self._logger = logging.getLogger("plant_defense_pipeline")
        self._logger.setLevel(getattr(logging, self.log_level.upper()))
        
        # Prevent duplicate handlers if logger is re-initialized
        if self._logger.handlers:
            self._logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, self.log_level.upper()))
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)
        
        # File handler with rotation
        log_file = self.log_dir / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, self.log_level.upper()))
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)
        
        # Also log to a generic 'latest.log' for easy access
        latest_log = self.log_dir / "latest.log"
        latest_handler = logging.FileHandler(latest_log, mode='w')
        latest_handler.setLevel(getattr(logging, self.log_level.upper()))
        latest_handler.setFormatter(formatter)
        self._logger.addHandler(latest_handler)
        
        self._setup_complete = True
        self._logger.info("Pipeline logger initialized")

    def get_logger(self) -> logging.Logger:
        """Return the underlying logging.Logger instance."""
        return self._logger

    def set_level(self, level: str):
        """Dynamically change the log level."""
        log_level = getattr(logging, level.upper())
        self._logger.setLevel(log_level)
        for handler in self._logger.handlers:
            handler.setLevel(log_level)
        self._logger.info(f"Log level changed to {level}")

    def log_pipeline_start(self, config: Dict[str, Any]):
        """Log the start of a pipeline run with configuration details."""
        self._logger.info("=" * 80)
        self._logger.info("PIPELINE START")
        self._logger.info(f"Timestamp: {datetime.now().isoformat()}")
        self._logger.info(f"Python Version: {sys.version}")
        self._logger.info(f"Working Directory: {os.getcwd()}")
        self._logger.info("Configuration:")
        for key, value in config.items():
            self._logger.info(f"  {key}: {value}")
        self._logger.info("=" * 80)

    def log_pipeline_end(self, status: str, duration_seconds: float):
        """Log the end of a pipeline run."""
        self._logger.info("=" * 80)
        self._logger.info(f"PIPELINE END - Status: {status}")
        self._logger.info(f"Duration: {duration_seconds:.2f} seconds")
        self._logger.info("=" * 80)

    def log_artifact_created(self, artifact_path: str, artifact_type: str, checksum: Optional[str] = None):
        """Log the creation of a data artifact."""
        msg = f"Artifact created: {artifact_path} (Type: {artifact_type})"
        if checksum:
            msg += f" | Checksum: {checksum}"
        self._logger.info(msg)

    def log_warning(self, message: str):
        """Log a warning message."""
        self._logger.warning(message)

    def log_error(self, message: str):
        """Log an error message."""
        self._logger.error(message)

    def log_critical(self, message: str):
        """Log a critical message."""
        self._logger.critical(message)

    def log_debug(self, message: str):
        """Log a debug message."""
        self._logger.debug(message)


def setup_logging(log_level: str = "INFO", log_dir: Optional[Path] = None) -> PipelineLogger:
    """
    Initialize the pipeline logger.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files. Uses config default if None.
    
    Returns:
        PipelineLogger instance
    """
    return PipelineLogger(log_level=log_level, log_dir=log_dir)


def set_log_level(level: str):
    """
    Convenience function to change the log level of the active logger.
    
    Args:
        level: New log level string
    """
    logger_instance = PipelineLogger()
    logger_instance.set_level(level)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance, optionally with a specific name.
    
    Args:
        name: Optional name for the logger. If None, returns the main pipeline logger.
    
    Returns:
        logging.Logger instance
    """
    if name is None:
        return PipelineLogger().get_logger()
    else:
        # Return a child logger
        return logging.getLogger(f"plant_defense_pipeline.{name}")
