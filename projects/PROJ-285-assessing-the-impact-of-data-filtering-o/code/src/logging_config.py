import logging
import sys
import os
from pathlib import Path
from typing import Optional

# Custom Exception Hierarchy for the Pipeline
class PipelineError(Exception):
    """Base exception for all pipeline errors."""
    pass

class DataIngestionError(PipelineError):
    """Raised when data loading or ingestion fails."""
    pass

class ThresholdFilterError(PipelineError):
    """Raised when threshold filtering logic encounters an error."""
    pass

class CoordinateMatchError(PipelineError):
    """Raised when coordinate matching fails or tolerance is exceeded."""
    pass

class StatisticalAnalysisError(PipelineError):
    """Raised during statistical calculations or model fitting."""
    pass

class ConfigError(PipelineError):
    """Raised when configuration validation fails."""
    pass


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Retrieves a configured logger instance.
    Ensures the logger is configured only once to avoid duplicate handlers.
    """
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.DEBUG)

    # Create console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)

    # Create file handler
    log_dir = Path("data")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "pipeline.log"
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)

    return logger


def get_log_file_path() -> Path:
    """Returns the path to the current log file."""
    return Path("data/pipeline.log")


def configure_logging(log_level: int = logging.INFO, log_file: Optional[str] = None):
    """
    Global configuration for logging.
    Can be called in main entry points to set specific levels or output paths.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to prevent duplicates if called multiple times
    root_logger.handlers.clear()

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(log_level)
    ch.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    root_logger.addHandler(ch)

    # File handler
    if log_file is None:
        log_file = "data/pipeline.log"
    
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    root_logger.addHandler(fh)


class SafeExecutionBlock:
    """
    Context manager to wrap execution blocks with try/except logic,
    ensuring errors are logged as specific pipeline exceptions rather than generic ones.
    """
    def __init__(self, operation_name: str, logger: Optional[logging.Logger] = None):
        self.operation_name = operation_name
        self.logger = logger or get_logger()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.logger.error(f"Error during {self.operation_name}: {exc_val}", exc_info=True)
            # Re-raise as a specific PipelineError if it isn't already
            if not isinstance(exc_val, PipelineError):
                raise PipelineError(f"Failed {self.operation_name}: {exc_val}") from exc_val
            raise exc_val
        return False
