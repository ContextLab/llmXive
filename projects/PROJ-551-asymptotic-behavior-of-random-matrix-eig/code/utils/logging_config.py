import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union

from utils.config import get_project_paths


class SimulationJsonFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records as structured JSON.
    Ensures all log entries satisfy Constitution Principle I (Reproducibility)
    by including timestamps, seed states, and parameter snapshots.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Attach extra structured data if present
        if hasattr(record, "simulation_params"):
            log_entry["simulation_params"] = record.simulation_params
        if hasattr(record, "seed_state"):
            log_entry["seed_state"] = record.seed_state
        if hasattr(record, "data_path"):
            log_entry["data_path"] = record.data_path

        return json.dumps(log_entry)


def setup_simulation_logger(
    log_file_path: Optional[Union[str, Path]] = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Configure a dedicated logger for simulation runs that writes structured
    JSON logs to the specified file path.

    Args:
        log_file_path: Path to the log file. Defaults to data/logs/simulation_run.log.
        level: Logging level (default: INFO).

    Returns:
        Configured logger instance.
    """
    if log_file_path is None:
        paths = get_project_paths()
        log_dir = paths["data"] / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file_path = log_dir / "simulation_run.log"
    else:
        log_file_path = Path(log_file_path)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("simulation")
    logger.setLevel(level)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        logger.handlers.clear()

    file_handler = logging.FileHandler(log_file_path)
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
    num_eigenvalues: int = 10,
    **extra_params: Any,
) -> None:
    """
    Logs the start of a simulation run with full parameter reproducibility.

    Args:
        logger: The configured logger instance.
        seed: Random seed used for this run.
        matrix_size: Dimension N of the Wigner matrix.
        perturbation_norm: Norm (theta) of the perturbation.
        perturbation_type: Type of perturbation (e.g., 'diagonal', 'block_sparse').
        sparsity_density: Density parameter if applicable.
        num_eigenvalues: Number of top eigenvalues to compute.
        **extra_params: Additional parameters to include in the log.
    """
    seed_state = {
        "global_seed": seed,
        "numpy_seed": int(seed),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    params = {
        "matrix_size": matrix_size,
        "perturbation_norm": perturbation_norm,
        "perturbation_type": perturbation_type,
        "num_eigenvalues": num_eigenvalues,
        **extra_params,
    }
    if sparsity_density is not None:
        params["sparsity_density"] = sparsity_density

    logger.info(
        "Simulation started",
        extra={"seed_state": seed_state, "simulation_params": params},
    )


def log_simulation_end(
    logger: logging.Logger,
    execution_time_seconds: float,
    status: str = "success",
    error_message: Optional[str] = None,
) -> None:
    """
    Logs the end of a simulation run.

    Args:
        logger: The configured logger instance.
        execution_time_seconds: Total runtime of the simulation.
        status: 'success' or 'failed'.
        error_message: Error details if status is 'failed'.
    """
    end_params = {
        "execution_time_seconds": execution_time_seconds,
        "status": status,
    }
    if error_message:
        end_params["error"] = error_message

    logger.info(
        "Simulation ended",
        extra={"simulation_params": end_params},
    )


def log_eigenvalue_results(
    logger: logging.Logger,
    eigenvalues: list,
    outlier_indices: Optional[list] = None,
    theoretical_edge: float = 2.0,
) -> None:
    """
    Logs the computed eigenvalues and outlier detection results.

    Args:
        logger: The configured logger instance.
        eigenvalues: List of computed eigenvalues (sorted descending).
        outlier_indices: Indices of eigenvalues identified as outliers.
        theoretical_edge: Theoretical bulk edge (default 2.0 for Wigner).
    """
    results = {
        "top_eigenvalues": eigenvalues,
        "outlier_indices": outlier_indices,
        "theoretical_edge": theoretical_edge,
        "outlier_count": len(outlier_indices) if outlier_indices else 0,
    }

    logger.info(
        "Eigenvalue results computed",
        extra={"simulation_params": results},
    )
