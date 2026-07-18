import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .config import get_project_paths


class SimulationJsonFormatter(logging.Formatter):
    """
    Custom JSON formatter for simulation logs.
    Ensures all log records are valid JSON objects with consistent structure.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data

        return json.dumps(log_entry)


def setup_simulation_logger(
    log_file_path: Optional[str] = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Set up a structured JSON logger for simulation runs.

    Args:
        log_file_path: Path to the log file. If None, uses default from config.
        level: Logging level.

    Returns:
        Configured logger instance.
    """
    if log_file_path is None:
        paths = get_project_paths()
        log_dir = paths["data"] / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file_path = str(log_dir / "simulation_run.log")

    # Ensure parent directory exists
    Path(log_file_path).parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("simulation")
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # File handler with JSON formatter
    file_handler = logging.FileHandler(log_file_path, mode="w")
    file_handler.setFormatter(SimulationJsonFormatter())
    logger.addHandler(file_handler)

    return logger


def log_simulation_start(
    logger: logging.Logger,
    seed: int,
    matrix_size: int,
    perturbation_norm: float,
    perturbation_type: str,
    sparsity_density: Optional[float] = None,
    rank: Optional[int] = None,
    **kwargs: Any,
) -> None:
    """
    Log the start of a simulation run with all parameters.

    Args:
        logger: The configured logger.
        seed: Random seed used.
        matrix_size: Size of the Wigner matrix (N).
        perturbation_norm: Norm of the perturbation (theta).
        perturbation_type: Type of perturbation (e.g., 'diagonal', 'sparse').
        sparsity_density: Sparsity density if applicable.
        rank: Rank of the perturbation if applicable.
        **kwargs: Additional parameters to log.
    """
    extra_data = {
        "event": "simulation_start",
        "seed": seed,
        "matrix_size": matrix_size,
        "perturbation_norm": perturbation_norm,
        "perturbation_type": perturbation_type,
    }

    if sparsity_density is not None:
        extra_data["sparsity_density"] = sparsity_density

    if rank is not None:
        extra_data["rank"] = rank

    extra_data.update(kwargs)

    logger.info(
        "Simulation started",
        extra={"extra_data": extra_data},
    )


def log_simulation_end(
    logger: logging.Logger,
    execution_time_seconds: float,
    status: str,
    error: Optional[str] = None,
) -> None:
    """
    Log the end of a simulation run.

    Args:
        logger: The configured logger.
        execution_time_seconds: Total execution time.
        status: Status of the run (e.g., 'success', 'failed').
        error: Error message if failed.
    """
    extra_data = {
        "event": "simulation_end",
        "execution_time_seconds": execution_time_seconds,
        "status": status,
    }

    if error is not None:
        extra_data["error"] = error

    logger.info(
        "Simulation finished",
        extra={"extra_data": extra_data},
    )


def log_eigenvalue_results(
    logger: logging.Logger,
    eigenvalues: list[float],
    outlier_indices: list[int],
    bulk_edge: float = 2.0,
    bbp_threshold: Optional[float] = None,
) -> None:
    """
    Log eigenvalue results and outlier detection.

    Args:
        logger: The configured logger.
        eigenvalues: List of computed eigenvalues.
        outlier_indices: Indices of detected outliers.
        bulk_edge: Theoretical bulk edge (default 2.0).
        bbp_threshold: Predicted BBP threshold if available.
    """
    extra_data = {
        "event": "eigenvalue_results",
        "eigenvalues": eigenvalues,
        "outlier_indices": outlier_indices,
        "bulk_edge": bulk_edge,
        "num_outliers": len(outlier_indices),
    }

    if bbp_threshold is not None:
        extra_data["bbp_threshold"] = bbp_threshold

    logger.info(
        "Eigenvalue analysis complete",
        extra={"extra_data": extra_data},
    )
