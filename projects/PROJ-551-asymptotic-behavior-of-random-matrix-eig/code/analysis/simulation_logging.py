"""
Structured logging for simulation run parameters.

This module implements structured JSON logging for simulation runs to satisfy
Constitution Principle I (Reproducibility). It logs the exact random seed state,
parameter values, and timestamp for every simulation execution.

Output: data/logs/simulation_run.log
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

# Project paths
from utils.config import get_project_paths


class SimulationJsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON with simulation-specific fields."""
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields if present
        if hasattr(record, "simulation_data"):
            log_data.update(record.simulation_data)

        # Add standard fields
        if hasattr(record, "run_id"):
            log_data["run_id"] = record.run_id
        if hasattr(record, "N"):
            log_data["N"] = record.N
        if hasattr(record, "seed"):
            log_data["seed"] = record.seed
        if hasattr(record, "theta"):
            log_data["theta"] = record.theta
        if hasattr(record, "perturbation_type"):
            log_data["perturbation_type"] = record.perturbation_type

        return json.dumps(log_data)


def setup_simulation_logger(
    log_path: Optional[str] = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Set up the simulation logger with JSON formatting.

    Args:
        log_path: Path to the log file. Defaults to data/logs/simulation_run.log
        level: Logging level

    Returns:
        Configured logger instance
    """
    paths = get_project_paths()
    if log_path is None:
        log_path = str(paths["data_logs"] / "simulation_run.log")

    # Ensure directory exists
    log_dir = Path(log_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger("simulation")
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # File handler with JSON formatter
    file_handler = logging.FileHandler(log_path, mode="a")
    file_handler.setLevel(level)
    file_handler.setFormatter(SimulationJsonFormatter())

    logger.addHandler(file_handler)

    return logger


def log_simulation_start(
    logger: logging.Logger,
    run_id: str,
    N: int,
    seed: int,
    theta: float,
    perturbation_type: str = "diagonal",
    rank: int = 1,
    support_density: Optional[float] = None,
) -> None:
    """
    Log the start of a simulation run with all parameters.

    Args:
        logger: Logger instance
        run_id: Unique run identifier
        N: Matrix dimension
        seed: Random seed value
        theta: Perturbation strength
        perturbation_type: Type of perturbation (diagonal, block-sparse, random sparse)
        rank: Rank of perturbation
        support_density: Support density for sparse perturbations
    """
    extra_data = {
        "run_id": run_id,
        "N": N,
        "seed": seed,
        "theta": theta,
        "perturbation_type": perturbation_type,
        "rank": rank,
        "support_density": support_density,
    }

    logger.info(
        "Simulation run started",
        extra={"simulation_data": extra_data, **extra_data},
    )


def log_simulation_end(
    logger: logging.Logger,
    run_id: str,
    eigenvalues: list,
    outlier_flag: bool,
    execution_time_seconds: float,
) -> None:
    """
    Log the completion of a simulation run with results.

    Args:
        logger: Logger instance
        run_id: Unique run identifier
        eigenvalues: List of computed eigenvalues
        outlier_flag: Whether an outlier was detected
        execution_time_seconds: Time taken for the simulation
    """
    extra_data = {
        "run_id": run_id,
        "eigenvalues": eigenvalues,
        "outlier_flag": outlier_flag,
        "execution_time_seconds": execution_time_seconds,
    }

    logger.info(
        "Simulation run completed",
        extra={"simulation_data": extra_data, **extra_data},
    )


def log_parameter_sweep(
    logger: logging.Logger,
    sweep_id: str,
    parameter_name: str,
    parameter_values: list,
    N: int,
    num_seeds: int,
) -> None:
    """
    Log the start of a parameter sweep.

    Args:
        logger: Logger instance
        sweep_id: Unique sweep identifier
        parameter_name: Name of the swept parameter (e.g., 'theta', 'density')
        parameter_values: List of parameter values to sweep
        N: Matrix dimension
        num_seeds: Number of seeds per configuration
    """
    extra_data = {
        "sweep_id": sweep_id,
        "parameter_name": parameter_name,
        "parameter_values": parameter_values,
        "N": N,
        "num_seeds": num_seeds,
    }

    logger.info(
        f"Parameter sweep started: {parameter_name}",
        extra={"simulation_data": extra_data, **extra_data},
    )


def main() -> None:
    """
    Main entry point for testing the logging functionality.

    This function demonstrates the logging capabilities by running a
    sample simulation and logging all relevant parameters and results.
    """
    logger = setup_simulation_logger()

    # Sample run parameters
    run_id = "test_run_001"
    N = 1000
    seed = 42
    theta = 2.5
    perturbation_type = "diagonal"
    rank = 1

    # Log simulation start
    log_simulation_start(
        logger=logger,
        run_id=run_id,
        N=N,
        seed=seed,
        theta=theta,
        perturbation_type=perturbation_type,
        rank=rank,
    )

    # Simulate some results (in real usage, these would come from simulation_loop)
    eigenvalues = [2.45, 1.98, 1.95, 1.92, 1.90]
    outlier_flag = True
    execution_time = 0.123

    # Log simulation end
    log_simulation_end(
        logger=logger,
        run_id=run_id,
        eigenvalues=eigenvalues,
        outlier_flag=outlier_flag,
        execution_time_seconds=execution_time,
    )

    print(f"Structured logs written to: {get_project_paths()['data_logs'] / 'simulation_run.log'}")


if __name__ == "__main__":
    main()
