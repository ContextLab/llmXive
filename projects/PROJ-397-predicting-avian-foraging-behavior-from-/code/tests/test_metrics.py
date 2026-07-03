"""
Test suite for metric calculations.
Verifies correctness of model evaluation metrics.
"""
import os
import sys
import unittest
import numpy as np
from pathlib import Path

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

def calculate_metrics(y_true, y_pred):
    """
    Calculate balanced accuracy and per-class F1 scores.
    
    Currently returns dummy values to indicate the implementation is pending
    (as per task requirement for a failing stub).
    """
    # TODO: Implement actual metric calculation logic using sklearn
    # 1. Calculate balanced accuracy
    # 2. Calculate per-class F1 scores
    # 3. Return a dictionary of metrics
    return {
        "balanced_accuracy": 0.0,
        "per_class_f1": {}
    }

class TestMetrics(unittest.TestCase):

    def test_metrics_calc(self):
        """
        Test the calculation of balanced accuracy and per-class F1 scores.
        
        This test is currently expected to fail as the implementation is a stub.
        It expects the calculate_metrics function to return valid results
        that match expected values for a known input.
        """
        # Define a simple test case
        y_true = np.array([0, 1, 2, 0, 1, 2])
        y_pred = np.array([0, 1, 1, 0, 1, 2]) # One misclassification in class 2
        
        # Calculate metrics (currently returns zeros/dummy)
        metrics = calculate_metrics(y_true, y_pred)
        
        # Check that balanced accuracy is not the default dummy value (0.0)
        # In a real scenario, we would check against a specific expected value.
        # For now, we assert it's not the stub value to force implementation.
        self.assertNotEqual(metrics["balanced_accuracy"], 0.0, 
                            "Metrics calculation is not implemented (returns dummy value).")
        
        # Assert that per_class_f1 is populated
        self.assertTrue(len(metrics["per_class_f1"]) > 0, 
                        "Per-class F1 scores are not populated.")

        # If we reach here, the stub was replaced. 
        # A more rigorous test would verify specific values.
        # Example: expected_balanced_acc = 0.916...
        # self.assertAlmostEqual(metrics["balanced_accuracy"], expected_balanced_acc, places=2)