"""
Integration module for simulation logging.
Wraps the SimulationProgressLogger to provide high-level logging functions
for the coverage simulation pipeline.
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from .progress_logger import SimulationProgressLogger
from .logging_config import setup_simulation_logger


def create_simulation_logging_integration(
    output_dir: Optional[Path] = None,
    log_level: int = logging.INFO
) -> SimulationProgressLogger:
    """
    Initialize and return a configured SimulationProgressLogger.

    Args:
        output_dir: Directory where log files will be written. Defaults to project root.
        log_level: Logging level (e.g., logging.INFO, logging.DEBUG).

    Returns:
        Configured SimulationProgressLogger instance.
    """
    logger = setup_simulation_logger(
        logger_name="simulation_progress",
        log_level=log_level,
        output_dir=output_dir
    )
    return SimulationProgressLogger(logger)


def log_simulation_condition(
    logger: SimulationProgressLogger,
    dataset: str,
    epsilon: float,
    noise_type: str,
    statistic: str,
    sample_size: int,
    seed: int,
    status: str = "START"
) -> None:
    """
    Log the start, progress, or completion of a specific simulation condition.

    This function formats a structured log message containing the key parameters
    of the current simulation run (dataset, epsilon, noise type, statistic, etc.)
    and the current status (START, PROGRESS, COMPLETE, ERROR).

    Args:
        logger: The SimulationProgressLogger instance.
        dataset: Name of the dataset being processed (e.g., 'adult', 'iris').
        epsilon: The differential privacy budget (epsilon) value.
        noise_type: Type of noise applied ('laplace' or 'gaussian').
        statistic: The statistic being computed ('mean' or 'regression_coefficient').
        sample_size: Number of samples drawn for this iteration.
        seed: Random seed used for reproducibility.
        status: Status of the condition ('START', 'PROGRESS', 'COMPLETE', 'ERROR').
    """
    message = (
        f"[{status}] Condition: dataset={dataset}, "
        f"epsilon={epsilon:.4f}, noise_type={noise_type}, "
        f"statistic={statistic}, sample_size={sample_size}, seed={seed}"
    )

    if status == "START":
        logger.info(message)
    elif status == "COMPLETE":
        logger.info(message)
    elif status == "ERROR":
        logger.error(message)
    else:
        logger.debug(message)
