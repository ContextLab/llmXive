import logging
import os
import random
import sys
import time
import hashlib
from typing import Optional, Dict, Any
from pathlib import Path

# Ensure the log directory exists if configured
LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

class PipelineLogger:
    """
    A logger wrapper that enforces reproducible logging by managing
    random seeds and recording step timing.
    """

    def __init__(self, name: str, level: int = logging.INFO, log_file: Optional[str] = None):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False  # Avoid duplicate logs if root is configured

        # Clear existing handlers to ensure clean state
        if self.logger.handlers:
            self.logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)

        # File handler (optional)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(level)
            file_handler.setFormatter(console_format)
            self.logger.addHandler(file_handler)

        self.start_times: Dict[str, float] = {}

    def set_seed(self, seed: int):
        """Set global random seeds for reproducibility."""
        random.seed(seed)
        # Try to set numpy seed if available, but don't fail if not
        try:
            import numpy as np
            np.random.seed(seed)
        except ImportError:
            pass
        
        # Log the seed for auditability
        seed_hash = hashlib.sha256(str(seed).encode()).hexdigest()[:8]
        self.logger.info(f"Reproducibility: Random seed set to {seed} (hash: {seed_hash})")

    def timed_step(self, step_name: str, start: bool = True):
        """
        Context manager or manual timer for step timing.
        If start=True, records the start time.
        If start=False, calculates duration and logs it.
        """
        if start:
            self.start_times[step_name] = time.time()
            self.logger.info(f"Starting step: {step_name}")
            return step_name
        else:
            if step_name in self.start_times:
                duration = time.time() - self.start_times[step_name]
                self.logger.info(f"Completed step: {step_name} in {duration:.4f} seconds")
                del self.start_times[step_name]
            else:
                self.logger.warning(f"Step {step_name} completed but was not started.")
            return duration

    def info(self, msg: str, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def debug(self, msg: str, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        self.logger.critical(msg, *args, **kwargs)


_logger_instance: Optional[PipelineLogger] = None

def get_logger(name: str = "turbulence_pipeline", log_file: Optional[str] = None) -> PipelineLogger:
    """
    Factory function to get or create a PipelineLogger instance.
    Uses a singleton pattern per name to avoid duplicate handlers.
    """
    global _logger_instance
    if _logger_instance is None or _logger_instance.name != name:
        _logger_instance = PipelineLogger(name, log_file=log_file)
    return _logger_instance


def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None) -> PipelineLogger:
    """
    Convenience function to setup the primary logger.
    """
    return get_logger("turbulence_pipeline", log_file=log_file)


def timed_step(step_name: str, start: bool = True) -> Optional[float]:
    """
    Convenience function to use the global logger's timer.
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = PipelineLogger("turbulence_pipeline")
    return _logger_instance.timed_step(step_name, start)
