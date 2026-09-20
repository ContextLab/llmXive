"""
Test suite for metrics calculation functions.

This task implements a failing stub as per T006b specification:
- Defines calculate_metrics function (placeholder)
- Defines TestMetrics class with test_metrics_calc that asserts False
- Verifies pytest returns exit code 1 when run
"""
import os
import sys
import unittest
import numpy as np
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from utils.config import get_models_dir


def calculate_metrics(y_true, y_pred):
    """
    Calculate classification metrics.
    
    This is a placeholder implementation for T006b.
    The actual implementation will be done in T018.
    
    Args:
        y_true: Array-like of true labels
        y_pred: Array-like of predicted labels
        
    Returns:
        dict: Dictionary containing balanced accuracy and per-class F1 scores
    """
    # Placeholder - will be implemented in T018
    raise NotImplementedError("calculate_metrics not yet implemented - see T018")


class TestMetrics(unittest.TestCase):
    """Test cases for metrics calculation."""
    
    def test_metrics_calc(self):
        """
        Failing stub test as per T006b specification.
        
        This test currently asserts False to ensure pytest returns exit code 1.
        It will be replaced with actual metric validation tests in T018.
        """
        # T006b requirement: failing stub that asserts False
        self.assertFalse(True, "This is a failing stub for T006b. Will be replaced in T018 with real metric tests.")
        
    def test_calculate_metrics_not_implemented(self):
        """Verify that calculate_metrics raises NotImplementedError."""
        y_true = np.array([0, 1, 0, 1])
        y_pred = np.array([0, 1, 1, 0])
        
        with self.assertRaises(NotImplementedError):
            calculate_metrics(y_true, y_pred)


if __name__ == '__main__':
    # Run tests and verify exit code
    unittest.main()