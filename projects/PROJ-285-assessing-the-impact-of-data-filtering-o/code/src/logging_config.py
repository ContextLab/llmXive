import logging
import sys
import os
from pathlib import Path
from typing import Optional

class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass

class DataIngestionError(PipelineError):
    """Exception for data loading issues."""
    pass

class ThresholdFilterError(PipelineError):
    """Exception for filtering logic issues."""
    pass

class CoordinateMatchError(PipelineError):
    """Exception for coordinate matching issues."""
    pass

class StatisticalAnalysisError(PipelineError):
    """Exception for statistical calculation issues."""
    pass

class ConfigError(PipelineError):
    """Exception for configuration issues."""
    pass

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance configured for the pipeline.
    
    Args:
        name: The name of the logger (usually __name__).
        
    Returns:
        Configured Logger instance.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # File handler
    log_dir = Path("data") / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "pipeline.log"
    
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    return logger

def get_log_file_path() -> Path:
    """Returns the path to the main log file."""
    return Path("data") / "logs" / "pipeline.log"

def configure_logging():
    """Configure global logging settings."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

class SafeExecutionBlock:
    """Context manager for safe execution of pipeline blocks."""
    def __init__(self, block_name: str):
        self.block_name = block_name
        self.logger = get_logger(__name__)

    def __enter__(self):
        self.logger.info(f"Starting block: {self.block_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.logger.error(f"Block {self.block_name} failed with {exc_type.__name__}: {exc_val}")
        else:
            self.logger.info(f"Block {self.block_name} completed successfully.")
        return False  # Do not suppress exceptions