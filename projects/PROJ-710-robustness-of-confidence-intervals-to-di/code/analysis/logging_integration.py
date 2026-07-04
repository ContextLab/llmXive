"""
Logging integration for User Story 2 adjustments.
Records which adjustment methods were applied and the resulting coverage rates.
"""
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from .logging_config import setup_simulation_logger
from .progress_logger import SimulationProgressLogger


def log_adjustment_application(
    logger: logging.Logger,
    dataset: str,
    epsilon: float,
    noise_type: str,
    statistic: str,
    adjustment_method: str,
    unadjusted_coverage: float,
    adjusted_coverage: float,
    improvement_delta: float
) -> None:
    """
    Log the application of an adjustment method and its effect on coverage.

    Args:
        logger: The logger instance to use.
        dataset: Name of the dataset (e.g., 'UCI Adult').
        epsilon: Privacy budget value.
        noise_type: Type of noise applied ('Laplace' or 'Gaussian').
        statistic: The statistic being analyzed ('mean' or 'regression_coefficient').
        adjustment_method: Name of the adjustment method applied.
        unadjusted_coverage: Coverage rate before adjustment.
        adjusted_coverage: Coverage rate after adjustment.
        improvement_delta: Difference between adjusted and unadjusted coverage.
    """
    message = (
        f"Adjustment Applied | Dataset: {dataset}, Epsilon: {epsilon:.4f}, "
        f"Noise: {noise_type}, Statistic: {statistic}, "
        f"Method: {adjustment_method} | "
        f"Unadjusted: {unadjusted_coverage:.4f}, Adjusted: {adjusted_coverage:.4f}, "
        f"Delta: {improvement_delta:.4f}"
    )
    logger.info(message)


def log_coverage_summary(
    logger: logging.Logger,
    results: List[Dict[str, Any]]
) -> None:
    """
    Log a summary of coverage rates for all conditions.

    Args:
        logger: The logger instance to use.
        results: List of dictionaries containing coverage results.
    """
    logger.info("=== Coverage Results Summary ===")
    for result in results:
        dataset = result.get('dataset', 'Unknown')
        epsilon = result.get('epsilon', 0.0)
        noise_type = result.get('noise_type', 'Unknown')
        statistic = result.get('statistic', 'Unknown')
        adjustment_method = result.get('adjustment_method', 'None')
        adjusted_coverage = result.get('adjusted_coverage', 0.0)
        improvement_delta = result.get('improvement_delta', 0.0)

        logger.info(
            f"  {dataset} | eps={epsilon:.4f} | {noise_type} | {statistic} | "
            f"{adjustment_method} -> Coverage: {adjusted_coverage:.4f} "
            f"(Δ={improvement_delta:+.4f})"
        )
    logger.info("=== End Summary ===")


def create_adjustment_logging_integration(
    log_file_path: Optional[Path] = None,
    level: int = logging.INFO
) -> logging.Logger:
    """
    Create and configure a logger specifically for adjustment logging.

    Args:
        log_file_path: Path to the log file. If None, logs to console only.
        level: Logging level.

    Returns:
        Configured logger instance.
    """
    logger_name = "adjustment_logging"
    logger = setup_simulation_logger(
        name=logger_name,
        log_file_path=log_file_path,
        level=level
    )
    return logger


def log_adjustment_results_to_file(
    results: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Save adjustment results to a JSON file for later inspection.

    Args:
        results: List of result dictionaries.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)