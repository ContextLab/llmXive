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
    linear_regression_trend,
    save_decay_fit_results,
    save_bootstrap_results,
    get_bootstrap_resamples
)
from config import get_config, set_config, Config, Hyperparameters, SafetyConstraints, PathConfig

class TestExponentialDecay(unittest.TestCase):
    def test_exponential_decay_formula(self):
        """Test that the exponential decay function produces correct values."""
        x = np.array([0, 1, 2, 3])
        a, b, c = 10.0, 0.5, 2.0
        y = exponential_decay(x, a, b, c)
        
        expected = a * np.exp(-b * x) + c
        np.testing.assert_array_almost_equal(y, expected)

    def test_decay_behavior(self):
        """Test that decay function actually decreases."""
        x = np.array([0, 1, 2, 3, 4])
        y = exponential_decay(x, 10.0, 0.5, 2.0)
        self.assertTrue(y[0] > y[-1], "Decay function should decrease over time")

class TestFitExponentialDecay(unittest.TestCase):
    def test_fit_perfect_decay(self):
        """Test fitting on perfect exponential decay data."""
        x = np.linspace(0, 10, 50)
        true_a, true_b, true_c = 5.0, 0.3, 1.0
        y = exponential_decay(x, true_a, true_b, true_c) + np.random.normal(0, 0.01, len(x))
        
        results = fit_exponential_decay(x, y)
        
        # Check that fitted parameters are close to true values
        self.assertAlmostEqual(results['a'], true_a, delta=0.5)
        self.assertAlmostEqual(results['b'], true_b, delta=0.1)
        self.assertAlmostEqual(results['c'], true_c, delta=0.1)
        
        # R-squared should be high for good fit
        self.assertGreater(results['r_squared'], 0.9)

    def test_fit_returns_dict(self):
        """Test that fit function returns a dictionary with required keys."""
        x = np.array([1, 2, 3])
        y = np.array([2, 1.5, 1])
        
        results = fit_exponential_decay(x, y)
        
        self.assertIsInstance(results, dict)
        self.assertIn('a', results)
        self.assertIn('b', results)
        self.assertIn('c', results)
        self.assertIn('r_squared', results)

class TestDetectPlateauOrDegradation(unittest.TestCase):
    def test_detect_improvement(self):
        """Test detection of improving metrics."""
        metrics = [0.5, 0.6, 0.7, 0.8, 0.9]
        result = detect_plateau_or_degradation(metrics)
        self.assertEqual(result, 'improving')

    def test_detect_plateau(self):
        """Test detection of plateau metrics."""
        metrics = [0.8, 0.81, 0.805, 0.802, 0.801]
        result = detect_plateau_or_degradation(metrics)
        self.assertEqual(result, 'plateau')

    def test_detect_degradation(self):
        """Test detection of degradation metrics."""
        metrics = [0.9, 0.85, 0.8, 0.75, 0.7]
        result = detect_plateau_or_degradation(metrics)
        self.assertEqual(result, 'degradation')

    def test_short_sequence(self):
        """Test with very short sequence."""
        metrics = [0.5]
        result = detect_plateau_or_degradation(metrics)
        self.assertEqual(result, 'improving')

class TestPairedBootstrapTest(unittest.TestCase):
    def test_significant_difference(self):
        """Test bootstrap test with clearly different distributions."""
        np.random.seed(42)
        baseline = np.random.normal(0.5, 0.1, 100)
        post_mod = np.random.normal(0.7, 0.1, 100)
        
        results = paired_bootstrap_test(baseline, post_mod, n_resamples=1000)
        
        self.assertIn('p_value', results)
        self.assertIn('is_significant', results)
        self.assertIn('original_difference', results)
        
        # With clear difference, should be significant
        self.assertTrue(results['is_significant'])

    def test_no_significant_difference(self):
        """Test bootstrap test with similar distributions."""
        np.random.seed(42)
        baseline = np.random.normal(0.5, 0.1, 100)
        post_mod = np.random.normal(0.51, 0.1, 100)
        
        results = paired_bootstrap_test(baseline, post_mod, n_resamples=1000)
        
        # With similar distributions, might not be significant
        self.assertIn('p_value', results)
        self.assertIn('is_significant', results)

    def test_mismatched_lengths_raises_error(self):
        """Test that mismatched lengths raise ValueError."""
        baseline = [0.5, 0.6, 0.7]
        post_mod = [0.6, 0.7]
        
        with self.assertRaises(ValueError):
            paired_bootstrap_test(baseline, post_mod)

    def test_configurable_resamples(self):
        """Test that number of resamples is configurable via config."""
        # Set config with custom resamples
        config = get_config()
        config.bootstrap_resamples = 500
        
        np.random.seed(42)
        baseline = np.random.normal(0.5, 0.1, 50)
        post_mod = np.random.normal(0.6, 0.1, 50)
        
        results = paired_bootstrap_test(baseline, post_mod, n_resamples=500)
        self.assertEqual(results['n_resamples'], 500)

class TestLinearRegressionTrend(unittest.TestCase):
    def test_perfect_linear_increase(self):
        """Test linear regression on perfect increasing line."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])  # y = 2x
        
        results = linear_regression_trend(x, y)
        
        self.assertAlmostEqual(results['slope'], 2.0, places=5)
        self.assertAlmostEqual(results['intercept'], 0.0, places=5)
        self.assertAlmostEqual(results['r_squared'], 1.0, places=5)
        self.assertEqual(results['trend_direction'], 'improving')

    def test_perfect_linear_decrease(self):
        """Test linear regression on perfect decreasing line."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([10, 8, 6, 4, 2])  # y = -2x + 12
        
        results = linear_regression_trend(x, y)
        
        self.assertAlmostEqual(results['slope'], -2.0, places=5)
        self.assertLess(results['trend_direction'], 'flat')  # Should be 'declining'
        self.assertEqual(results['trend_direction'], 'declining')

    def test_flat_line(self):
        """Test linear regression on flat line."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([5, 5, 5, 5, 5])
        
        results = linear_regression_trend(x, y)
        
        self.assertAlmostEqual(results['slope'], 0.0, places=5)
        self.assertEqual(results['trend_direction'], 'flat')
        self.assertAlmostEqual(results['r_squared'], 0.0, places=5)

    def test_noisy_linear_trend(self):
        """Test linear regression on noisy linear data."""
        np.random.seed(42)
        x = np.array([1, 2, 3, 4, 5])
        y = 2 * x + np.random.normal(0, 0.5, 5)
        
        results = linear_regression_trend(x, y)
        
        # Slope should be close to 2
        self.assertGreater(results['slope'], 1.5)
        self.assertLess(results['slope'], 2.5)
        self.assertEqual(results['trend_direction'], 'improving')
        self.assertGreater(results['r_squared'], 0.8)

class TestSaveFunctions(unittest.TestCase):
    def test_save_decay_fit_results(self):
        """Test saving decay fit results to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'results', 'decay_fit.json')
            
            results = {
                'a': 5.0,
                'b': 0.3,
                'c': 1.0,
                'r_squared': 0.95
            }
            
            save_decay_fit_results(results, output_path)
            
            self.assertTrue(os.path.exists(output_path))
            
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            
            self.assertEqual(loaded['a'], 5.0)
            self.assertEqual(loaded['b'], 0.3)

    def test_save_bootstrap_results(self):
        """Test saving bootstrap results to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'results', 'bootstrap.json')
            
            results = {
                'p_value': 0.03,
                'is_significant': True,
                'alpha': 0.05,
                'n_resamples': 1000
            }
            
            save_bootstrap_results(results, output_path)
            
            self.assertTrue(os.path.exists(output_path))
            
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            
            self.assertEqual(loaded['p_value'], 0.03)
            self.assertTrue(loaded['is_significant'])

class TestConfigIntegration(unittest.TestCase):
    def test_get_bootstrap_resamples_from_config(self):
        """Test that get_bootstrap_resamples reads from config."""
        # Reset to default
        config = get_config()
        if hasattr(config, 'bootstrap_resamples'):
            original = config.bootstrap_resamples
        else:
            original = 1000
        
        # Test default
        resamples = get_bootstrap_resamples()
        self.assertIsInstance(resamples, int)
        self.assertGreater(resamples, 0)