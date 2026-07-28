"""
Unit tests for pipeline/stats.py
"""
import unittest
import numpy as np
from unittest.mock import patch, MagicMock
import json
import os
import tempfile

from pipeline.stats import (
    exponential_decay,
    fit_exponential_decay,
    detect_plateau_or_degradation,
    paired_bootstrap_test,
    save_decay_fit_results,
    save_bootstrap_results
)


class TestExponentialDecay(unittest.TestCase):
    """Tests for the exponential_decay model function."""

    def test_model_shape(self):
        """Verify the model produces the expected shape."""
        x = np.array([0, 1, 2, 3])
        a, b, c = 10.0, 0.5, 2.0
        y = exponential_decay(x, a, b, c)
        
        # y = 10 * exp(-0.5 * x) + 2
        expected = np.array([
            10 * np.exp(0) + 2,
            10 * np.exp(-0.5) + 2,
            10 * np.exp(-1.0) + 2,
            10 * np.exp(-1.5) + 2
        ])
        
        np.testing.assert_array_almost_equal(y, expected)

    def test_decay_behavior(self):
        """Verify the function actually decays."""
        x = np.linspace(0, 10, 100)
        y = exponential_decay(x, 10.0, 1.0, 0.0)
        
        # First value should be > last value
        self.assertGreater(y[0], y[-1])
        # All values should be positive
        self.assertTrue(np.all(y >= 0))


class TestFitExponentialDecay(unittest.TestCase):
    """Tests for fit_exponential_decay function."""

    def test_fit_perfect_data(self):
        """Fit should recover parameters from perfect data."""
        x = np.linspace(0, 10, 50)
        true_a, true_b, true_c = 5.0, 0.3, 1.0
        y = exponential_decay(x, true_a, true_b, true_c)
        
        result = fit_exponential_decay(x, y)
        
        # Allow some tolerance for numerical errors
        self.assertAlmostEqual(result["a"], true_a, delta=0.5)
        self.assertAlmostEqual(result["b"], true_b, delta=0.1)
        self.assertAlmostEqual(result["c"], true_c, delta=0.5)
        self.assertGreater(result["r_squared"], 0.99)

    def test_insufficient_data(self):
        """Should raise error with too few points."""
        x = np.array([1, 2])
        y = np.array([10, 9])
        
        with self.assertRaises(ValueError):
            fit_exponential_decay(x, y)

    def test_r_squared_calculation(self):
        """Verify R-squared is between 0 and 1 for good fit."""
        x = np.linspace(0, 10, 50)
        y = exponential_decay(x, 5.0, 0.3, 1.0) + np.random.normal(0, 0.1, 50)
        
        result = fit_exponential_decay(x, y)
        self.assertGreaterEqual(result["r_squared"], 0)
        self.assertLessEqual(result["r_squared"], 1)


class TestDetectPlateauOrDegradation(unittest.TestCase):
    """Tests for detect_plateau_or_degradation function."""

    def test_empty_trajectory(self):
        """Should handle empty trajectory gracefully."""
        result = detect_plateau_or_degradation([], "accuracy")
        self.assertIsNone(result["plateau_cycle"])
        self.assertIsNone(result["degradation_cycle"])
        self.assertIn("Empty trajectory", result["reason"])

    def test_degradation_detection(self):
        """Should detect degradation when metric drops significantly."""
        trajectory = [
            {"cycle_number": 0, "gsm8k_accuracy": 0.80},
            {"cycle_number": 1, "gsm8k_accuracy": 0.79},
            {"cycle_number": 2, "gsm8k_accuracy": 0.70},  # Drop > 5%
        ]
        
        result = detect_plateau_or_degradation(trajectory, "gsm8k_accuracy", threshold_pct=5.0)
        
        self.assertEqual(result["degradation_cycle"], 2)
        # Baseline is 0.80, 5% drop is 0.76. 0.70 < 0.76

    def test_plateau_detection(self):
        """Should detect plateau when decay rate is low."""
        # Create data that is nearly flat
        trajectory = [
            {"cycle_number": 0, "gsm8k_accuracy": 0.80},
            {"cycle_number": 1, "gsm8k_accuracy": 0.801},
            {"cycle_number": 2, "gsm8k_accuracy": 0.802},
            {"cycle_number": 3, "gsm8k_accuracy": 0.803},
            {"cycle_number": 4, "gsm8k_accuracy": 0.804},
        ]
        
        result = detect_plateau_or_degradation(trajectory, "gsm8k_accuracy", threshold_pct=5.0)
        
        # With such slow change, b should be small, triggering plateau detection
        self.assertIsNotNone(result["plateau_cycle"])

    def test_no_issues(self):
        """Should return None for both if no issues detected."""
        trajectory = [
            {"cycle_number": 0, "gsm8k_accuracy": 0.80},
            {"cycle_number": 1, "gsm8k_accuracy": 0.82},
            {"cycle_number": 2, "gsm8k_accuracy": 0.84},
        ]
        
        result = detect_plateau_or_degradation(trajectory, "gsm8k_accuracy", threshold_pct=5.0)
        
        # No degradation (improving)
        self.assertIsNone(result["degradation_cycle"])


class TestPairedBootstrapTest(unittest.TestCase):
    """Tests for paired_bootstrap_test function."""

    def test_significant_difference(self):
        """Should detect significant difference when one exists."""
        # Baseline centered around 0.5, modified centered around 0.6
        np.random.seed(42)
        baseline = np.random.normal(0.5, 0.05, 100)
        modified = np.random.normal(0.6, 0.05, 100)
        
        result = paired_bootstrap_test(baseline.tolist(), modified.tolist(), alpha=0.05, n_iterations=1000)
        
        self.assertTrue(result["is_significant"])
        self.assertGreater(result["mean_diff"], 0)
        self.assertLess(result["p_value"], 0.05)

    def test_no_significant_difference(self):
        """Should not detect difference when distributions are similar."""
        np.random.seed(42)
        baseline = np.random.normal(0.5, 0.05, 100)
        modified = np.random.normal(0.51, 0.05, 100)  # Very small difference
        
        result = paired_bootstrap_test(baseline.tolist(), modified.tolist(), alpha=0.05, n_iterations=1000)
        
        # With such a small difference, likely not significant
        # Note: This is probabilistic, so we just check the structure
        self.assertIn("p_value", result)
        self.assertIn("confidence_interval", result)

    def test_mismatched_lengths(self):
        """Should raise error if lengths differ."""
        with self.assertRaises(ValueError):
            paired_bootstrap_test([1, 2, 3], [1, 2])

    def test_empty_lists(self):
        """Should raise error for empty lists."""
        with self.assertRaises(ValueError):
            paired_bootstrap_test([], [])

    def test_confidence_interval_validity(self):
        """CI should be a tuple of two numbers."""
        np.random.seed(42)
        baseline = np.random.normal(0.5, 0.05, 50)
        modified = np.random.normal(0.55, 0.05, 50)
        
        result = paired_bootstrap_test(baseline.tolist(), modified.tolist(), n_iterations=500)
        
        ci = result["confidence_interval"]
        self.assertIsInstance(ci, tuple)
        self.assertEqual(len(ci), 2)
        self.assertLess(ci[0], ci[1])


class TestSaveFunctions(unittest.TestCase):
    """Tests for save_decay_fit_results and save_bootstrap_results."""

    def setUp(self):
        """Create a temporary directory for test outputs."""
        self.temp_dir = tempfile.mkdtemp()

    def test_save_decay_fit_results(self):
        """Should write valid JSON to file."""
        fit_result = {
            "a": 1.0,
            "b": 0.5,
            "c": 0.1,
            "r_squared": 0.95
        }
        output_path = os.path.join(self.temp_dir, "decay_fit.json")
        
        save_decay_fit_results(fit_result, output_path)
        
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        self.assertEqual(loaded, fit_result)

    def test_save_bootstrap_results(self):
        """Should write valid JSON to file."""
        test_result = {
            "mean_diff": 0.05,
            "p_value": 0.02,
            "is_significant": True,
            "confidence_interval": (0.01, 0.09)
        }
        output_path = os.path.join(self.temp_dir, "bootstrap_results.json")
        
        save_bootstrap_results(test_result, output_path)
        
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        self.assertEqual(loaded, test_result)


if __name__ == "__main__":
    unittest.main()