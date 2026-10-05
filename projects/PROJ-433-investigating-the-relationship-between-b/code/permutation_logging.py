"""
Module T036: Add logging for permutation test execution and results.

This module integrates with code/analysis.py to log permutation test
execution details and results to data/analysis_log.txt as required by US4.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

from utils import setup_logger


def log_permutation_start(
    logger: logging.Logger,
    n_shuffles: int,
    seed: int,
    metric_name: str,
    behavior_name: str
) -> None:
    """Log the start of a permutation test.

    Args:
        logger: The logger instance to write to.
        n_shuffles: Number of shuffles to perform.
        seed: Random seed used for reproducibility.
        metric_name: Name of the metric being tested.
        behavior_name: Name of the behavioral variable.
    """
    logger.info(f"Starting permutation test: {metric_name} vs {behavior_name}")
    logger.info(f"Parameters: n_shuffles={n_shuffles}, seed={seed}")


def log_permutation_result(
    logger: logging.Logger,
    observed_stat: float,
    p_value: float,
    null_distribution: np.ndarray,
    metric_name: str,
    behavior_name: str
) -> None:
    """Log the results of a permutation test.

    Args:
        logger: The logger instance to write to.
        observed_stat: The observed correlation statistic.
        p_value: The permutation-derived p-value.
        null_distribution: Array of statistics from shuffled data.
        metric_name: Name of the metric being tested.
        behavior_name: Name of the behavioral variable.
    """
    logger.info(f"Permutation test completed: {metric_name} vs {behavior_name}")
    logger.info(f"Observed statistic: {observed_stat:.6f}")
    logger.info(f"Permutation p-value: {p_value:.6f}")
    logger.info(f"Null distribution stats: mean={np.mean(null_distribution):.6f}, "
                f"std={np.std(null_distribution):.6f}")
    logger.info(f"Null distribution range: [{np.min(null_distribution):.6f}, "
                f"{np.max(null_distribution):.6f}]")


def log_permutation_test_summary(
    logger: logging.Logger,
    total_subjects: int,
    excluded_subjects: int,
    successful_tests: int,
    failed_tests: int
) -> None:
    """Log a summary of the permutation testing run.

    Args:
        logger: The logger instance to write to.
        total_subjects: Total number of subjects considered.
        excluded_subjects: Number of subjects excluded due to QC/data issues.
        successful_tests: Number of successful permutation tests.
        failed_tests: Number of permutation tests that failed.
    """
    logger.info("Permutation testing summary:")
    logger.info(f"  Total subjects: {total_subjects}")
    logger.info(f"  Excluded subjects: {excluded_subjects}")
    logger.info(f"  Successful tests: {successful_tests}")
    logger.info(f"  Failed tests: {failed_tests}")


def main() -> None:
    """Demonstrate the logging functions (for manual testing)."""
    logger = setup_logger("analysis")
    
    # Simulate a permutation test run
    log_permutation_start(
        logger,
        n_shuffles=1000,
        seed=42,
        metric_name="transition_count",
        behavior_name="DSST_score"
    )
    
    observed_stat = 0.45
    p_value = 0.032
    null_dist = np.random.normal(0, 0.1, 1000)
    
    log_permutation_result(
        logger,
        observed_stat=observed_stat,
        p_value=p_value,
        null_distribution=null_dist,
        metric_name="transition_count",
        behavior_name="DSST_score"
    )
    
    log_permutation_test_summary(
        logger,
        total_subjects=50,
        excluded_subjects=5,
        successful_tests=1,
        failed_tests=0
    )


if __name__ == "__main__":
    main()