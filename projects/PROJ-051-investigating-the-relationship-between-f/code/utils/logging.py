"""
Reproducible logging utilities for the turbulence analysis pipeline.

Features:
- Configurable random seeds for reproducibility.
- Step timing tracking (start/stop/elapsed).
- Structured logging with correlation IDs for pipeline steps.
"""

import logging
import os
import random
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Generator, Optional

from config import get_config


# Default log format
_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class PipelineLogger:
    """
    A logger wrapper that adds reproducibility features:
    - Random seed management
    - Step timing
    - Context-aware logging
    """

    def __init__(
        self,
        name: str = "turbulence_pipeline",
        level: int = logging.INFO,
        log_file: Optional[str] = None,
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Prevent duplicate handlers if re-initialized
        if not self.logger.handlers:
            # Console handler
            ch = logging.StreamHandler(sys.stdout)
            ch.setLevel(level)
            formatter = logging.Formatter(_LOG_FORMAT, _DATE_FORMAT)
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

            # File handler (optional)
            if log_file:
                os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else ".", exist_ok=True)
                fh = logging.FileHandler(log_file)
                fh.setLevel(level)
                fh.setFormatter(formatter)
                self.logger.addHandler(fh)

        self._step_timings: Dict[str, float] = {}
        self._current_step: Optional[str] = None

    def set_seed(self, seed: int) -> None:
        """
        Set random seeds for reproducibility across numpy, random, and torch (if available).
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

        self.logger.info(f"Random seed set to: {seed}")

    def log_step_start(self, step_name: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log the start of a pipeline step and start timing."""
        self._current_step = step_name
        self._step_timings[step_name] = time.time()

        msg = f"Starting step: {step_name}"
        if metadata:
            msg += f" | Metadata: {metadata}"
        self.logger.info(msg)

    def log_step_end(self, step_name: Optional[str] = None, success: bool = True) -> None:
        """Log the end of a pipeline step and record elapsed time."""
        target_step = step_name or self._current_step
        if not target_step:
            self.logger.warning("No active step to end.")
            return

        if target_step not in self._step_timings:
            self.logger.warning(f"Step {target_step} was not started.")
            return

        start_time = self._step_timings.pop(target_step)
        elapsed = time.time() - start_time

        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"Step {target_step} {status} | Elapsed: {elapsed:.2f}s")

        self._current_step = None

    @contextmanager
    def timed_step(self, step_name: str, metadata: Optional[Dict[str, Any]] = None) -> Generator[None, None, None]:
        """
        Context manager to automatically log start/end and timing for a step.
        """
        self.log_step_start(step_name, metadata)
        try:
            yield
            self.log_step_end(step_name, success=True)
        except Exception as e:
            self.logger.error(f"Step {step_name} raised exception: {e}")
            self.log_end(step_name, success=False)
            raise

def get_logger(
    name: str = "turbulence_pipeline",
    log_file: Optional[str] = None,
) -> PipelineLogger:
    """
    Factory function to get a configured PipelineLogger.
    """
    # Try to get config for default log level/file if not provided
    try:
        config = get_config()
        log_level = getattr(logging, config.log_level.upper(), logging.INFO)
        default_log_file = config.log_file if hasattr(config, 'log_file') else None
    except Exception:
        log_level = logging.INFO
        default_log_file = None

    if log_file is None:
        log_file = default_log_file

    return PipelineLogger(name=name, level=log_level, log_file=log_file)


# Convenience function for quick setup
def setup_logging(
    seed: Optional[int] = None,
    log_file: Optional[str] = None,
    level: str = "INFO",
) -> PipelineLogger:
    """
    Initialize logging with optional seed and file output.
    """
    logger = get_logger(log_file=log_file)
    logger.logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if seed is not None:
        logger.set_seed(seed)

    return logger