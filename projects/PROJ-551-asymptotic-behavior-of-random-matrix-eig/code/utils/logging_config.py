"""
Structured logging configuration for simulation runs.
Implements Constitution Principle I (Reproducibility) by capturing
exact random seed states, parameter values, and timestamps in JSON format.
"""
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .config import get_project_paths


class SimulationJsonFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records as JSON.
    Ensures reproducibility by including seed state and run metadata.
    """

    def __init__(self, seed_state: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.seed_state = seed_state or {}

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include seed state if available for reproducibility
        if self.seed_state:
            log_entry["seed_state"] = self.seed_state

        # Include extra fields if present
        if hasattr(record, "params"):
            log_entry["params"] = record.params

        if hasattr(record, "run_id"):
            log_entry["run_id"] = record.run_id

        return json.dumps(log_entry)


def setup_simulation_logger(
    seed_state: Optional[Dict[str, Any]] = None,
    log_file_name: str = "simulation_run.log",
    log_level: int = logging.INFO,
) -> logging.Logger:
    """
    Configure a structured JSON logger for simulation runs.

    Args:
        seed_state: Dictionary containing random seed states (numpy, random, torch, etc.)
        log_file_name: Name of the log file relative to data/logs/
        log_level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    # Get project paths and ensure log directory exists
    paths = get_project_paths()
    log_dir = paths["data"] / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file_path = log_dir / log_file_name

    # Create logger
    logger = logging.getLogger("simulation")
    logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create file handler with JSON formatter
    file_handler = logging.FileHandler(log_file_path, mode="a")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(SimulationJsonFormatter(seed_state))

    logger.addHandler(file_handler)

    return logger


def log_simulation_start(
    logger: logging.Logger,
    params: Dict[str, Any],
    seed_state: Dict[str, Any],
    run_id: Optional[str] = None,
) -> None:
    """
    Log the start of a simulation run with full parameter and seed state.

    Args:
        logger: The configured logger instance
        params: Dictionary of simulation parameters
        seed_state: Dictionary of random seed states
        run_id: Optional unique run identifier
    """
    extra = {"params": params, "seed_state": seed_state}
    if run_id:
        extra["run_id"] = run_id

    logger.info("Simulation run started", extra=extra)


def log_simulation_end(
    logger: logging.Logger,
    status: str,
    duration_seconds: Optional[float] = None,
    run_id: Optional[str] = None,
) -> None:
    """
    Log the completion of a simulation run.

    Args:
        logger: The configured logger instance
        status: Status string (e.g., "success", "failed", "interrupted")
        duration_seconds: Optional execution duration
        run_id: Optional unique run identifier
    """
    extra = {"status": status}
    if duration_seconds is not None:
        extra["duration_seconds"] = duration_seconds
    if run_id:
        extra["run_id"] = run_id

    logger.info("Simulation run completed", extra=extra)


def log_eigenvalue_results(
    logger: logging.Logger,
    eigenvalues: list,
    outlier_indices: list,
    perturbation_norm: float,
    matrix_size: int,
    run_id: Optional[str] = None,
) -> None:
    """
    Log eigenvalue analysis results.

    Args:
        logger: The configured logger instance
        eigenvalues: List of computed eigenvalues
        outlier_indices: Indices of detected outliers
        perturbation_norm: Norm of the perturbation matrix
        matrix_size: Size of the matrix
        run_id: Optional unique run identifier
    """
    extra = {
        "eigenvalues": eigenvalues,
        "outlier_indices": outlier_indices,
        "perturbation_norm": perturbation_norm,
        "matrix_size": matrix_size,
    }
    if run_id:
        extra["run_id"] = run_id

    logger.info("Eigenvalue results computed", extra=extra)
