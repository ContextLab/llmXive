"""
Logging utilities for the pipeline.
"""
import logging
import os
from pathlib import Path
from typing import Optional
import time

from config import load_paths


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Setup logging configuration.

    Args:
        log_level: The logging level (e.g., 'INFO', 'DEBUG').

    Returns:
        The root logger.
    """
    paths = load_paths()
    log_dir = paths.get("logs", Path("data/logs"))
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    log_file = Path(log_dir) / "pipeline.log"

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    return logging.getLogger(__name__)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.

    Args:
        name: The logger name.

    Returns:
        The logger instance.
    """
    return logging.getLogger(name)


class PhaseTimer:
    """
    Timer for tracking the duration of pipeline phases.
    """

    def __init__(self, phase_name: str, logger: Optional[logging.Logger] = None):
        """
        Initialize the PhaseTimer.

        Args:
            phase_name: The name of the phase.
            logger: Optional logger instance.
        """
        self.phase_name = phase_name
        self.logger = logger or get_logger(__name__)
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def start(self) -> None:
        """Start the timer."""
        self.start_time = time.time()
        self.logger.info(f"Starting phase: {self.phase_name}")

    def stop(self) -> float:
        """
        Stop the timer and return the duration.

        Returns:
            The duration in seconds.
        """
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        self.logger.info(f"Completed phase: {self.phase_name} in {duration:.2f} seconds")
        return duration

    def __enter__(self) -> "PhaseTimer":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()
