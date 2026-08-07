import logging
import os
import random
import sys
import time
import hashlib
from contextlib import contextmanager
from typing import Optional, Generator
from datetime import datetime

# Ensure the package structure allows imports from utils
# This file is located at code/utils/logging.py

def _get_run_id() -> str:
    """Generate a unique run ID based on timestamp and a random salt."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    salt = str(random.randint(10000, 99999))
    raw = f"{timestamp}_{salt}"
    return hashlib.md5(raw.encode()).hexdigest()[:8]

class PipelineLogger:
    """
    A wrapper around Python's standard logging.Logger that adds:
    - Reproducible logging context (run_id)
    - Step timing utilities
    - Seed management
    """
    def __init__(self, name: str = "turbulence_pipeline", level: int = logging.INFO):
        self.run_id = _get_run_id()
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        if not self.logger.handlers:
            # Create console handler
            ch = logging.StreamHandler(sys.stdout)
            ch.setLevel(level)
            
            # Formatter with run_id and timestamp
            formatter = logging.Formatter(
                f"%(asctime)s [%(levelname)s] [RunID:{self.run_id}] "
                f"%(name)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

        # Add run_id to the logging context
        self.logger.info(f"Pipeline initialized with RunID: {self.run_id}")

    def set_seed(self, seed: int) -> None:
        """
        Set random seeds for reproducibility.
        Sets seed for: random, numpy (if available), and torch (if available).
        """
        random.seed(seed)
        try:
            import numpy as np
            np.random.seed(seed)
        except ImportError:
            pass
        
        try:
            import torch
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed)
        except ImportError:
            pass

        self.logger.info(f"Reproducibility: Random seed set to {seed}")

    def log_step_start(self, step_name: str) -> float:
        """
        Log the start of a pipeline step and return the start time.
        """
        self.logger.info(f"Step START: {step_name}")
        return time.perf_counter()

    def log_step_end(self, step_name: str, start_time: float) -> float:
        """
        Log the end of a pipeline step and return the duration.
        """
        duration = time.perf_counter() - start_time
        self.logger.info(f"Step END: {step_name} (Duration: {duration:.4f}s)")
        return duration

    @property
    def logger_instance(self) -> logging.Logger:
        """Expose the underlying logger instance for direct use if needed."""
        return self.logger

    def critical(self, msg: str) -> None:
        self.logger.critical(msg)

    def error(self, msg: str) -> None:
        self.logger.error(msg)

    def warning(self, msg: str) -> None:
        self.logger.warning(msg)

    def info(self, msg: str) -> None:
        self.logger.info(msg)

    def debug(self, msg: str) -> None:
        self.logger.debug(msg)

def get_logger(name: Optional[str] = None) -> PipelineLogger:
    """
    Factory function to get or create a PipelineLogger.
    If name is provided, uses that name; otherwise defaults to 'turbulence_pipeline'.
    """
    if name is None:
        name = "turbulence_pipeline"
    
    # Check if we already have a custom attribute attached to the standard logger
    # to avoid re-initializing handlers if this is called multiple times in the same process
    # However, for simplicity in this specific task, we return a fresh wrapper 
    # that shares the underlying logger state.
    base_logger = logging.getLogger(name)
    
    # We need to attach a custom attribute to the standard logger to hold our state
    # or just wrap it. Let's wrap it in a PipelineLogger instance.
    # To ensure we don't duplicate handlers, we check if the handler exists.
    
    # Since the API surface expects `from utils.logging import get_logger`, 
    # we return a configured instance.
    return PipelineLogger(name)

def setup_logging(log_level: str = "INFO", run_id: Optional[str] = None) -> PipelineLogger:
    """
    Setup the global logging configuration.
    Returns a configured PipelineLogger.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # If a specific run_id is needed, we could override the generator, 
    # but typically the logger creates one on init.
    logger = PipelineLogger(level=level)
    
    # Configure root logger if needed for third-party libraries
    logging.basicConfig(level=level, force=True)
    
    return logger

@contextmanager
def timed_step(logger: PipelineLogger, step_name: str) -> Generator[float, None, None]:
    """
    Context manager to time a specific step and log start/end automatically.
    
    Usage:
        logger = get_logger()
        with timed_step(logger, "compute_fractal"):
            # do work
            pass
    """
    start_time = logger.log_step_start(step_name)
    try:
        yield start_time
    finally:
        logger.log_step_end(step_name, start_time)