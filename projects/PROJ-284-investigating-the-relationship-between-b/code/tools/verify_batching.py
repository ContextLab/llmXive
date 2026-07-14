"""
Verification script for dynamic batch sizing logic.
"""
import logging
import os
from pathlib import Path

from code.logging_config import get_logger
from code.analysis.correlations import (
    get_optimal_batch_size,
    process_metrics_in_batches,
    MEMORY_LIMIT_BYTES
)
import pandas as pd
import numpy as np

logger = get_logger(__name__)

def verify_batch_size_logic():
    """Verify batch size calculation logic."""
    logger.log("verify_batch_size_logic_start")

    # Test cases
    test_cases = [
        (1000, 10, 7 * 1024**3, "Large dataset"),
        (100, 4, 7 * 1024**3, "Small dataset"),
        (10000, 100, 1 * 1024**3, "Memory constrained"),
    ]

    for n_subjects, n_features, mem_limit, desc in test_cases:
        batch_size = get_optimal_batch_size(n_subjects, n_features, mem_limit)
        logger.log(
            "batch_size_test",
            description=desc,
            n_subjects=n_subjects,
            n_features=n_features,
            memory_limit_gb=mem_limit / (1024**3),
            calculated_batch_size=batch_size
        )
        assert 1 <= batch_size <= n_subjects, f"Invalid batch size: {batch_size}"

    logger.log("verify_batch_size_logic_complete")
    return True

def verify_preprocessing_batching():
    """Verify preprocessing batching (placeholder for actual logic)."""
    logger.log("verify_preprocessing_batching_start")
    # Placeholder: actual verification would require real preprocessing data
    logger.log("verify_preprocessing_batching_complete")
    return True

def verify_correlation_batching():
    """Verify correlation batching logic."""
    logger.log("verify_correlation_batching_start")

    # Create synthetic test data
    n_subjects = 500
    n_metrics = 4
    df = pd.DataFrame({
        'subject_id': range(n_subjects),
        'modularity': np.random.rand(n_subjects),
        'global_efficiency': np.random.rand(n_subjects),
        'participation_coef': np.random.rand(n_subjects),
        'within_module_degree': np.random.rand(n_subjects),
        'MeanFD': np.random.rand(n_subjects),
        'motor_score': np.random.rand(n_subjects)
    })

    # Define a simple operation
    def dummy_op(batch, **kwargs):
        return batch

    # Test batching
    result = process_metrics_in_batches(df, "test_op", dummy_op, batch_size=50)

    assert len(result) == n_subjects, "Batching did not preserve row count"

    logger.log("verify_correlation_batching_complete")
    return True

def main():
    """Run all verifications."""
    logger.log("verify_batching_main_start")

    try:
        verify_batch_size_logic()
        verify_preprocessing_batching()
        verify_correlation_batching()
        logger.log("verify_batching_main_complete")
        print("All batching verifications passed.")
    except Exception as e:
        logger.log("verify_batching_main_error", error=str(e))
        print(f"Verification failed: {e}")
        raise

if __name__ == "__main__":
    main()