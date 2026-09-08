"""
Structured logging for simulation runs.

This module implements structured JSON logging for simulation parameters,
seed states, and execution metadata to satisfy Constitution Principle I
(Reproducibility).
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from utils.config import get_project_paths


class SimulationJsonFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured simulation logs.

    Converts log records into JSON objects containing:
    - timestamp (ISO 8601)
    - level
    - message
    - simulation metadata (run_id, seed, parameters)
    """

    def __init__(self):
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }

        # Extract simulation metadata from extra fields if present
        if hasattr(record, "run_id"):
            log_data["run_id"] = record.run_id
        if hasattr(record, "seed"):
            log_data["seed"] = record.seed
        if hasattr(record, "N"):
            log_data["N"] = record.N
        if hasattr(record, "theta"):
            log_data["theta"] = record.theta
        if hasattr(record, "perturbation_type"):
            log_data["perturbation_type"] = record.perturbation_type
        if hasattr(record, "rank"):
            log_data["rank"] = record.rank
        if hasattr(record, "support_density"):
            log_data["support_density"] = record.support_density
        if hasattr(record, "config"):
            log_data["config"] = record.config
        if hasattr(record, "execution_time"):
            log_data["execution_time"] = record.execution_time
        if hasattr(record, "status"):
            log_data["status"] = record.status

        return json.dumps(log_data)


def setup_simulation_logger(
    log_path: Optional[Path] = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Set up a logger for simulation runs with JSON formatting.

    Args:
        log_path: Path to the log file. If None, uses default project path.
        level: Logging level.

    Returns:
        Configured logger instance.
    """
    if log_path is None:
        paths = get_project_paths()
        log_path = paths["data_logs"] / "simulation_run.log"

    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("simulation")
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # File handler with JSON formatter
    file_handler = logging.FileHandler(log_path, mode='a')
    file_handler.setLevel(level)
    file_handler.setFormatter(SimulationJsonFormatter())

    logger.addHandler(file_handler)

    return logger


def log_simulation_start(
    logger: logging.Logger,
    run_id: str,
    seed: int,
    N: int,
    theta: float,
    perturbation_type: str,
    rank: int,
    support_density: Optional[float] = None,
    config: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log the start of a simulation run with all parameters.

    Args:
        logger: Logger instance.
        run_id: Unique run identifier.
        seed: Random seed used.
        N: Matrix dimension.
        theta: Perturbation strength.
        perturbation_type: Type of perturbation (diagonal, block-sparse, etc.).
        rank: Rank of perturbation.
        support_density: Density of non-zero elements (if applicable).
        config: Additional configuration dictionary.
    """
    extra = {
        "run_id": run_id,
        "seed": seed,
        "N": N,
        "theta": theta,
        "perturbation_type": perturbation_type,
        "rank": rank,
    }
    if support_density is not None:
        extra["support_density"] = support_density
    if config is not None:
        extra["config"] = config

    logger.info(
        f"Simulation run started: run_id={run_id}, N={N}, theta={theta}",
        extra=extra,
    )


def log_simulation_end(
    logger: logging.Logger,
    run_id: str,
    status: str,
    execution_time: float,
    eigenvalues: Optional[list] = None,
    outlier_flag: Optional[bool] = None,
) -> None:
    """
    Log the end of a simulation run with results.

    Args:
        logger: Logger instance.
        run_id: Unique run identifier.
        status: Completion status (success, failure, etc.).
        execution_time: Time taken in seconds.
        eigenvalues: List of computed eigenvalues (optional).
        outlier_flag: Whether an outlier was detected (optional).
    """
    extra = {
        "run_id": run_id,
        "status": status,
        "execution_time": execution_time,
    }
    if eigenvalues is not None:
        extra["eigenvalues"] = eigenvalues
    if outlier_flag is not None:
        extra["outlier_flag"] = outlier_flag

    logger.info(
        f"Simulation run completed: run_id={run_id}, status={status}",
        extra=extra,
    )


def log_parameter_sweep(
    logger: logging.Logger,
    sweep_name: str,
    parameters: Dict[str, Any],
    num_iterations: int,
) -> None:
    """
    Log the start of a parameter sweep.

    Args:
        logger: Logger instance.
        sweep_name: Name of the sweep.
        parameters: Dictionary of parameter ranges/values.
        num_iterations: Total number of iterations planned.
    """
    extra = {
        "sweep_name": sweep_name,
        "parameters": parameters,
        "num_iterations": num_iterations,
    }

    logger.info(
        f"Parameter sweep started: {sweep_name}",
        extra=extra,
    )


def main() -> None:
    """
    Test the simulation logging functionality.

    This function demonstrates the logging setup and logs a sample
    simulation run to verify the JSON formatting works correctly.
    """
    # Set up logger
    paths = get_project_paths()
    log_path = paths["data_logs"] / "simulation_run.log"
    logger = setup_simulation_logger(log_path)

    # Log a sample simulation
    run_id = "test_run_001"
    seed = 42
    N = 1000
    theta = 2.5
    perturbation_type = "diagonal"
    rank = 1
    support_density = 1.0

    log_simulation_start(
        logger,
        run_id=run_id,
        seed=seed,
        N=N,
        theta=theta,
        perturbation_type=perturbation_type,
        rank=rank,
        support_density=support_density,
        config={"tolerance": 1e-10, "num_eigenvalues": 10},
    )

    # Simulate some work
    import time
    time.sleep(0.1)

    # Log completion
    log_simulation_end(
        logger,
        run_id=run_id,
        status="success",
        execution_time=0.1,
        eigenvalues=[2.51, 2.1, 1.9, 1.8, 1.7],
        outlier_flag=True,
    )

    print(f"Simulation log written to: {log_path}")


if __name__ == "__main__":
    main()