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
    save_bootstrap_results,
    save_decay_fit_results
)

class TestExponentialDecay(unittest.TestCase):
    def test_exponential_decay_formula(self):
        """Test that exponential_decay function computes correct values."""
        x = np.array([0, 1, 2, 3])
        a, b, c = 10.0, 0.5, 2.0
        expected = a * np.exp(-b * x) + c
        result = exponential_decay(x, a, b, c)
        np.testing.assert_array_almost_equal(result, expected, decimal=5)

    def test_exponential_decay_parameters(self):
        """Test with different parameter values."""
        x = np.array([0, 1, 2])
        a, b, c = 5.0, 0.2, 1.0
        result = exponential_decay(x, a, b, c)
        self.assertEqual(len(result), 3)
        self.assertGreater(result[0], result[1])  # Should be decreasing

class TestFitExponentialDecay(unittest.TestCase):
    def test_fit_perfect_decay(self):
        """Test fitting on data generated from known exponential decay."""
        x = np.array([0, 1, 2, 3, 4, 5])
        true_a, true_b, true_c = 10.0, 0.3, 2.0
        y = true_a * np.exp(-true_b * x) + true_c + np.random.normal(0, 0.1, size=x.shape)
        
        np.random.seed(42)
        a, b, c = fit_exponential_decay(x, y)
        
        # Check that fitted parameters are close to true values
        self.assertAlmostEqual(a, true_a, delta=1.0)
        self.assertAlmostEqual(b, true_b, delta=0.2)
        self.assertAlmostEqual(c, true_c, delta=0.5)

    def test_fit_insufficient_points(self):
        """Test that fitting fails with too few points."""
        x = np.array([0, 1])
        y = np.array([1.0, 2.0])
        with self.assertRaises(ValueError):
            fit_exponential_decay(x, y)

class TestDetectPlateauOrDegradation(unittest.TestCase):
    def test_plateau_detection(self):
        """Test detection of plateau (b close to 0)."""
        params = (10.0, 0.001, 2.0)
        result = detect_plateau_or_degradation(params)
        self.assertEqual(result, 'plateau')

    def test_degradation_detection(self):
        """Test detection of degradation (a < 0)."""
        params = (-5.0, 0.5, 2.0)
        result = detect_plateau_or_degradation(params)
        self.assertEqual(result, 'degradation')

    def test_improving_detection(self):
        """Test detection of improving trend."""
        params = (10.0, 0.5, 2.0)
        result = detect_plateau_or_degradation(params)
        self.assertEqual(result, 'improving')

class TestPairedBootstrapTest(unittest.TestCase):
    @patch('config.get_config')
    def test_p_value_calculation(self, mock_get_config):
        """Test p-value calculation for known inputs."""
        mock_config = MagicMock()
        mock_config.hyperparameters.bootstrap_resamples = 1000
        mock_get_config.return_value = mock_config
        
        # Create two identical distributions - should have high p-value
        baseline = [1.0, 1.0, 1.0, 1.0, 1.0]
        modified = [1.0, 1.0, 1.0, 1.0, 1.0]
        
        result = paired_bootstrap_test(baseline, modified, resamples=1000)
        
        self.assertIn('p_value', result)
        self.assertIn('is_significant', result)
        self.assertIn('observed_difference', result)
        self.assertIn('ci_lower', result)
        self.assertIn('ci_upper', result)
        
        # With identical distributions, p-value should be high (not significant)
        self.assertTrue(result['p_value'] > 0.05)
        self.assertFalse(result['is_significant'])

    def test_different_distributions(self):
        """Test with clearly different distributions."""
        baseline = [1.0, 1.1, 0.9, 1.0, 1.0]
        modified = [2.0, 2.1, 1.9, 2.0, 2.0]
        
        result = paired_bootstrap_test(baseline, modified, resamples=1000)
        
        self.assertTrue(result['observed_difference'] > 0)
        # Should be significant given the large difference
        self.assertTrue(result['p_value'] < 0.05)
        self.assertTrue(result['is_significant'])

    def test_mismatched_lengths(self):
        """Test that mismatched lengths raise error."""
        baseline = [1.0, 1.0, 1.0]
        modified = [1.0, 1.0]
        with self.assertRaises(ValueError):
            paired_bootstrap_test(baseline, modified)

    def test_empty_lists(self):
        """Test that empty lists raise error."""
        with self.assertRaises(ValueError):
            paired_bootstrap_test([], [])

    @patch('config.get_config')
    def test_configurable_resamples(self, mock_get_config):
        """Test that resamples can be configured via config."""
        mock_config = MagicMock()
        mock_config.hyperparameters.bootstrap_resamples = 500
        mock_get_config.return_value = mock_config
        
        baseline = [1.0, 1.0, 1.0, 1.0, 1.0]
        modified = [1.0, 1.0, 1.0, 1.0, 1.0]
        
        result = paired_bootstrap_test(baseline, modified)
        self.assertEqual(result['resamples'], 500)

class TestLinearRegressionTrend(unittest.TestCase):
    def test_slope_calculation(self):
        """Test linear regression slope calculation."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])  # Perfect linear relationship: y = 2x
        
        result = linear_regression_trend(x, y)
        
        self.assertAlmostEqual(result['slope'], 2.0, places=5)
        self.assertAlmostEqual(result['intercept'], 0.0, places=5)
        self.assertAlmostEqual(result['r_squared'], 1.0, places=5)
        self.assertEqual(result['trend_direction'], 'improving')

    def test_negative_slope(self):
        """Test with negative slope (declining trend)."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([10, 8, 6, 4, 2])  # y = -2x + 12
        
        result = linear_regression_trend(x, y)
        
        self.assertAlmostEqual(result['slope'], -2.0, places=5)
        self.assertEqual(result['trend_direction'], 'declining')

    def test_flat_trend(self):
        """Test with flat trend (slope ~ 0)."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([5, 5, 5, 5, 5])
        
        result = linear_regression_trend(x, y)
        
        self.assertAlmostEqual(result['slope'], 0.0, places=5)
        self.assertEqual(result['trend_direction'], 'flat')

    def test_insufficient_points(self):
        """Test that insufficient points raise error."""
        x = np.array([1])
        y = np.array([1])
        with self.assertRaises(ValueError):
            linear_regression_trend(x, y)

    def test_constant_x(self):
        """Test that constant x values raise error."""
        x = np.array([1, 1, 1])
        y = np.array([1, 2, 3])
        with self.assertRaises(ValueError):
            linear_regression_trend(x, y)

class TestSaveFunctions(unittest.TestCase):
    def test_save_bootstrap_results(self):
        """Test saving bootstrap results to JSON."""
        results = {
            'p_value': 0.03,
            'is_significant': True,
            'observed_difference': 0.5
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, 'test_bootstrap.json')
            save_bootstrap_results(results, filepath)
            
            self.assertTrue(os.path.exists(filepath))
            with open(filepath, 'r') as f:
                loaded = json.load(f)
            self.assertEqual(loaded['p_value'], results['p_value'])

    def test_save_decay_fit_results(self):
        """Test saving decay fit results to JSON."""
        params = (10.0, 0.5, 2.0)
        trend = 'improving'
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, 'test_decay.json')
            save_decay_fit_results(params, trend, filepath)
            
            self.assertTrue(os.path.exists(filepath))
            with open(filepath, 'r') as f:
                loaded = json.load(f)
            self.assertEqual(loaded['a'], params[0])
            self.assertEqual(loaded['trend'], trend)

if __name__ == '__main__':
    unittest.main()