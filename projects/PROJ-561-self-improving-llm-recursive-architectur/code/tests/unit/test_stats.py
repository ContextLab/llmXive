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
    get_bootstrap_resamples,
    run_bootstrap_and_regression
)
from config import Config, Hyperparameters, set_config

class TestExponentialDecay(unittest.TestCase):
    def test_exponential_decay_function(self):
        x = np.array([0, 1, 2, 3])
        a, b, c = 10.0, 0.5, 1.0
        y = exponential_decay(x, a, b, c)
        # Check basic properties: decreasing, positive
        self.assertTrue(all(y > 0))
        self.assertTrue(y[0] > y[-1])

class TestFitExponentialDecay(unittest.TestCase):
    def test_fit_exponential_decay_success(self):
        # Generate synthetic data from known parameters
        x = np.linspace(0, 10, 20)
        true_a, true_b, true_c = 5.0, 0.3, 0.5
        y = true_a * np.exp(-true_b * x) + true_c + np.random.normal(0, 0.1, len(x))
        
        result = fit_exponential_decay(x, y)
        self.assertIsNotNone(result)
        self.assertIn('a', result)
        self.assertIn('b', result)
        self.assertIn('c', result)
        
    def test_fit_exponential_decay_failure(self):
        # Degenerate case: constant y
        x = np.array([1, 2, 3])
        y = np.array([5.0, 5.0, 5.0])
        result = fit_exponential_decay(x, y)
        # Should return None or handle gracefully
        self.assertIsNone(result)

class TestDetectPlateauOrDegradation(unittest.TestCase):
    def test_plateau_detection(self):
        y = np.array([1.0, 1.1, 1.05, 1.04, 1.03, 1.03, 1.03])
        result = detect_plateau_or_degradation(y)
        self.assertTrue(result['plateau'])
        self.assertFalse(result['degradation'])
        
    def test_degradation_detection(self):
        y = np.array([1.0, 1.5, 2.0, 1.8, 1.0, 0.5])
        result = detect_plateau_or_degradation(y)
        self.assertTrue(result['degradation'])
        
    def test_insufficient_data(self):
        y = np.array([1.0, 2.0])
        result = detect_plateau_or_degradation(y)
        self.assertIn('reason', result)

class TestPairedBootstrapTest(unittest.TestCase):
    def test_paired_bootstrap_test(self):
        baseline = [0.8, 0.82, 0.81, 0.79, 0.83]
        new = [0.85, 0.87, 0.86, 0.84, 0.88]
        
        result = paired_bootstrap_test(baseline, new, num_resamples=100, seed=42)
        
        self.assertIn('observed_difference', result)
        self.assertIn('p_value', result)
        self.assertIn('confidence_interval_95', result)
        self.assertIn('significant_at_0.05', result)
        self.assertGreater(result['observed_difference'], 0) # New is better
        
    def test_mismatched_lengths(self):
        with self.assertRaises(ValueError):
            paired_bootstrap_test([1, 2], [1, 2, 3])

class TestLinearRegressionTrend(unittest.TestCase):
    def test_linear_regression_positive_slope(self):
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 5, 4, 5]) # Roughly increasing
        result = linear_regression_trend(x, y)
        
        self.assertIn('slope', result)
        self.assertIn('intercept', result)
        self.assertIn('r_squared', result)
        self.assertGreater(result['slope'], 0)
        
    def test_linear_regression_perfect_fit(self):
        x = np.array([1, 2, 3, 4, 5])
        y = 2 * x + 1
        result = linear_regression_trend(x, y)
        
        self.assertAlmostEqual(result['slope'], 2.0, places=5)
        self.assertAlmostEqual(result['intercept'], 1.0, places=5)
        self.assertAlmostEqual(result['r_squared'], 1.0, places=5)

class TestSaveFunctions(unittest.TestCase):
    def test_save_bootstrap_results(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'test_bootstrap.json')
            data = {'p_value': 0.03, 'diff': 0.1}
            save_bootstrap_results(data, path)
            
            self.assertTrue(os.path.exists(path))
            with open(path, 'r') as f:
                loaded = json.load(f)
            self.assertEqual(loaded['p_value'], 0.03)
            
    def test_save_decay_fit_results(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'test_decay.json')
            data = {'a': 1.0, 'b': 0.5, 'c': 0.1}
            save_decay_fit_results(data, path)
            
            self.assertTrue(os.path.exists(path))
            with open(path, 'r') as f:
                loaded = json.load(f)
            self.assertEqual(loaded['a'], 1.0)

class TestGetBootstrapResamples(unittest.TestCase):
    def test_get_bootstrap_resamples_default(self):
        # Ensure config is set
        config = Config(
            hyperparameters=Hyperparameters(),
            safety_constraints=None,
            path_config=None
        )
        set_config(config)
        
        # Should return default if not set
        resamples = get_bootstrap_resamples()
        self.assertIsInstance(resamples, int)
        self.assertGreater(resamples, 0)

class TestRunBootstrapAndRegression(unittest.TestCase):
    def test_run_bootstrap_and_regression(self):
        baseline = [0.8, 0.81, 0.82]
        new = [0.85, 0.86, 0.87]
        cycle_indices = np.array([0, 1, 2])
        performance_history = [0.8, 0.85, 0.87]
        
        result = run_bootstrap_and_regression(
            baseline, new, cycle_indices, performance_history
        )
        
        self.assertIn('bootstrap_test', result)
        self.assertIn('regression_trend', result)
        self.assertIn('plateau_analysis', result)
        self.assertIn('num_resamples_used', result)
        
        # Check structure of sub-results
        self.assertIn('p_value', result['bootstrap_test'])
        self.assertIn('slope', result['regression_trend'])
        self.assertIn('plateau', result['plateau_analysis'])