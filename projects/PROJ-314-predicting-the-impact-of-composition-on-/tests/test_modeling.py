"""
Unit tests for the modeling module, specifically focusing on the baseline predictor logic.
"""
import unittest
import pandas as pd
import numpy as np
import sys
import os

# Add the code directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from modeling import evaluate_models


class TestBaselinePredictor(unittest.TestCase):
    """
    Test suite for the global mean baseline predictor functionality.
    Ensures that the baseline model correctly predicts the mean of the training target
    and that metrics are calculated accurately against this baseline.
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a deterministic dataset for testing
        np.random.seed(42)
        n_samples = 100

        # Generate synthetic features (not used by baseline, but required for signature)
        self.X_train = pd.DataFrame(np.random.rand(n_samples, 5), columns=['f1', 'f2', 'f3', 'f4', 'f5'])
        self.X_test = pd.DataFrame(np.random.rand(20, 5), columns=['f1', 'f2', 'f3', 'f4', 'f5'])

        # Generate target variable with a known mean
        self.y_train = pd.Series(np.random.normal(loc=50.0, scale=10.0, size=n_samples))
        self.y_test = pd.Series(np.random.normal(loc=50.0, scale=10.0, size=20))

        # Mock models dictionary with a 'baseline' entry
        # The baseline model is not a scikit-learn estimator, so we pass None or a mock
        # The function should handle the logic of generating predictions based on y_train mean
        self.models = {
            'baseline': None  # Indicates baseline logic should be used
        }

    def test_baseline_prediction_mean(self):
        """
        Test that the baseline predictor returns the global mean of the training set
        for all test samples.
        """
        expected_mean = self.y_train.mean()
        
        # Call the evaluation function
        metrics = evaluate_models(self.models, self.X_train, self.y_train, self.X_test, self.y_test)

        # The function should return a dictionary of metrics
        self.assertIn('baseline', metrics, "Baseline metrics should be present in the result")
        
        # Extract the baseline predictions if the function returns them, 
        # or verify the MAE/R2 against the theoretical baseline.
        # Since evaluate_models returns metrics, we check if the R2 is approx 0.0
        # and MAE is approx mean_absolute_error(y_test, y_train.mean())
        
        baseline_metrics = metrics['baseline']
        
        # Calculate expected MAE manually
        expected_mae = np.mean(np.abs(self.y_test - expected_mean))
        actual_mae = baseline_metrics['mae']

        self.assertAlmostEqual(actual_mae, expected_mae, places=5, 
                               msg=f"Baseline MAE {actual_mae} does not match expected {expected_mae}")

    def test_baseline_r_squared_zero(self):
        """
        Test that the R-squared score for the global mean baseline is approximately 0.0.
        A baseline that always predicts the mean should explain 0% of the variance.
        """
        metrics = evaluate_models(self.models, self.X_train, self.y_train, self.X_test, self.y_test)
        baseline_metrics = metrics['baseline']
        
        # R2 should be close to 0.0 (allowing for floating point error)
        # Note: If y_test variance is 0, R2 is undefined, but with random seed 42 it won't be.
        self.assertAlmostEqual(baseline_metrics['r2'], 0.0, places=5,
                               msg=f"Baseline R2 {baseline_metrics['r2']} should be approximately 0.0")

    def test_baseline_vs_random_model(self):
        """
        Test that the baseline predictor performs better than a random guess 
        (which would have a negative R2 on average) and establishes the floor.
        """
        metrics = evaluate_models(self.models, self.X_train, self.y_train, self.X_test, self.y_test)
        
        # The baseline R2 should be >= -1.0 (theoretical floor for R2)
        # In practice with random data, it should be very close to 0.
        self.assertGreaterEqual(metrics['baseline']['r2'], -0.1, 
                                msg="Baseline R2 should be at least -0.1 for this random dataset")

    def test_baseline_output_structure(self):
        """
        Test that the baseline output includes all required keys: MAE and R2.
        """
        metrics = evaluate_models(self.models, self.X_train, self.y_train, self.X_test, self.y_test)
        
        self.assertIn('baseline', metrics)
        self.assertIn('mae', metrics['baseline'])
        self.assertIn('r2', metrics['baseline'])

    def test_baseline_uses_training_mean_only(self):
        """
        Test that the baseline prediction is strictly the mean of the training set,
        and does not leak information from the test set.
        """
        # Create a scenario where test mean is different from train mean
        y_train_distinct = pd.Series([10, 10, 10, 10, 10])
        y_test_distinct = pd.Series([100, 100, 100, 100, 100])
        
        X_train_dummy = pd.DataFrame({'f1': [1, 2, 3, 4, 5]})
        X_test_dummy = pd.DataFrame({'f1': [1, 2, 3, 4, 5]})
        
        models = {'baseline': None}
        
        metrics = evaluate_models(models, X_train_dummy, y_train_distinct, X_test_dummy, y_test_distinct)
        
        # Expected prediction is 10.0 (mean of train)
        # Expected MAE is |100 - 10| = 90
        expected_mae = 90.0
        actual_mae = metrics['baseline']['mae']
        
        self.assertAlmostEqual(actual_mae, expected_mae, places=5,
                               msg=f"Baseline should use train mean (10), not test mean. MAE should be 90, got {actual_mae}")


if __name__ == '__main__':
    unittest.main()