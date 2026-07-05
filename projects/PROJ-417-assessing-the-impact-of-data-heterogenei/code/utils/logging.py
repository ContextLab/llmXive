"""Logging infrastructure for the meta-analysis simulation pipeline.

This module configures a centralized logging system that captures:
- Simulation progress (replicates, levels)
- Convergence failures (REML, optimization)
- General pipeline events

Output is written to: data/results/simulation.log
"""
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Ensure the data/results directory exists
LOG_DIR = Path("data/results")
LOG_FILE = LOG_DIR / "simulation.log"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Global logger instance
_logger: Optional[logging.Logger] = None


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    console: bool = True
) -> logging.Logger:
    """
    Configure the root logger for the pipeline.

    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
        log_file: Path to the log file. Defaults to data/results/simulation.log.
        console: Whether to log to stderr as well.

    Returns:
        The configured logger instance.
    """
    global _logger

    if _logger is not None:
        return _logger

    logger = logging.getLogger("llmXive")
    logger.setLevel(level)

    # Clear existing handlers to avoid duplicates in re-runs
    logger.handlers.clear()

    # Formatter for detailed output
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File Handler
    if log_file is None:
        log_file = LOG_FILE
    
    try:
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
    except Exception as e:
        # Fallback if file creation fails (e.g., permission issues)
        print(f"Warning: Could not create log file at {log_file}: {e}", file=sys.stderr)

    # Console Handler
    if console:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        logger.addHandler(console_handler)

    _logger = logger
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieve the configured logger.

    Args:
        name: Optional submodule name (e.g., "llmXive.generator").

    Returns:
        A logger instance.
    """
    global _logger
    if _logger is None:
        # Auto-initialize with defaults if not explicitly set up
        setup_logging()
    
    if name:
        return _logger.getChild(name)
    return _logger


# Convenience functions for specific log levels
def log_convergence_failure(estimator: str, study_id: str, message: str) -> None:
    """Log a specific convergence failure event."""
    logger = get_logger("convergence")
    logger.warning(f"CONVERGENCE FAILURE: {estimator} failed for study {study_id}: {message}")


def log_simulation_progress(current: int, total: int, level: float, replicate: int) -> None:
    """Log simulation progress."""
    logger = get_logger("simulation")
    logger.info(f"Progress: {current}/{total} (Level τ²={level}, Replicate {replicate})")
