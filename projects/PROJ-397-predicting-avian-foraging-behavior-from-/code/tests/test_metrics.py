"""
Test suite for metric calculations in the avian foraging behavior prediction pipeline.

This test file implements T006b:
- Contains a failing `test_metrics_calc` function stub that asserts False.
- Verifies that pytest returns exit code 1 when run.
"""
import os
import sys
import unittest
import numpy as np
from pathlib import Path

# Import config to ensure path consistency
from utils.config import get_seed


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """
    Placeholder metric calculation function.
    
    This function is a stub for future implementation.
    Currently, it does not perform real calculations.
    """
    # TODO: Implement actual metric calculations (accuracy, f1, etc.)
    return {
        'accuracy': 0.0,
        'f1_score': 0.0,
        'balanced_accuracy': 0.0
    }


class TestMetrics(unittest.TestCase):
    """Test cases for metric calculation functions."""

    def test_metrics_calc(self):
        """
        Stub test that currently fails.
        
        This test asserts False to verify that the test framework
        correctly identifies failing tests. This is part of T006b
        to ensure the test infrastructure is working before
        implementing actual metric logic.
        """
        # Generate dummy data for the stub
        y_true = np.array([0, 1, 0, 1, 1])
        y_pred = np.array([0, 0, 0, 1, 1])
        
        # Call the metric calculation function
        metrics = calculate_metrics(y_true, y_pred)
        
        # Stub assertion: This will fail until real metrics are implemented
        self.assertFalse(
            True, 
            "test_metrics_calc is a stub. Implement real metric calculations."
        )

    def test_seed_consistency(self):
        """Verify that the random seed is correctly retrieved."""
        seed = get_seed()
        self.assertIsInstance(seed, int)
        self.assertGreaterEqual(seed, 0)


if __name__ == '__main__':
    unittest.main()