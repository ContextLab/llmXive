"""
Unit tests for the permutation test implementation.
"""
import json
import os
import tempfile
import unittest
import numpy as np
from unittest.mock import patch, MagicMock

# Import the functions to test
from permutation_test import (
    calculate_permutation_pvalue,
    run_permutation_test,
    load_features,
    load_split_config,
    load_model
)
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge

class TestPermutationTest(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.features_path = os.path.join(self.temp_dir, "features.json")
        self.split_config_path = os.path.join(self.temp_dir, "split_config.json")
        self.model_path = os.path.join(self.temp_dir, "model.pkl")
        self.output_path = os.path.join(self.temp_dir, "results.json")

        # Create mock features data
        self.features_data = [
            {"sample_id": 1, "fidelity_loss": 0.5, "feature1": 0.1, "feature2": 0.2},
            {"sample_id": 2, "fidelity_loss": 0.6, "feature1": 0.3, "feature2": 0.4},
            {"sample_id": 3, "fidelity_loss": 0.7, "feature1": 0.5, "feature2": 0.6},
            {"sample_id": 4, "fidelity_loss": 0.8, "feature1": 0.7, "feature2": 0.8},
            {"sample_id": 5, "fidelity_loss": 0.9, "feature1": 0.9, "feature2": 1.0},
        ]
        
        with open(self.features_path, 'w') as f:
            json.dump(self.features_data, f)

        # Create mock split config
        self.split_config = {"train_indices": [0, 1, 2]}
        with open(self.split_config_path, 'w') as f:
            json.dump(self.split_config, f)

        # Create a simple mock model
        self.model = RandomForestRegressor(n_estimators=10, random_state=42)
        X_train = np.array([[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]])
        y_train = np.array([0.5, 0.6, 0.7])
        self.model.fit(X_train, y_train)
        
        import pickle
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_features(self):
        """Test loading features from JSON file."""
        data = load_features(self.features_path)
        self.assertEqual(len(data), 5)
        self.assertIn("fidelity_loss", data[0])

    def test_load_split_config(self):
        """Test loading split configuration."""
        config = load_split_config(self.split_config_path)
        self.assertEqual(config["train_indices"], [0, 1, 2])

    def test_load_model(self):
        """Test loading a trained model."""
        loaded_model = load_model(self.model_path)
        self.assertIsInstance(loaded_model, RandomForestRegressor)

    @patch('permutation_test.r2_score')
    def test_calculate_permutation_pvalue(self, mock_r2_score):
        """Test the permutation p-value calculation logic."""
        # Mock R2 scores
        mock_r2_score.side_effect = [0.9, 0.1, 0.2, 0.15, 0.05] # Observed, then 4 perms

        model = RandomForestRegressor(n_estimators=5, random_state=42)
        X_train = np.array([[0.1], [0.2], [0.3]])
        y_train = np.array([0.5, 0.6, 0.7])
        
        # Run with very few permutations for speed
        p_value, obs_r2, perms = calculate_permutation_pvalue(
            model, X_train, y_train, n_permutations=4, random_state=42
        )

        # 3 out of 4 permuted scores (0.1, 0.2, 0.15) are < 0.9, so p-value should be 0.25 (1/4)
        # Wait, logic: fraction of permuted >= observed.
        # Observed = 0.9. Perms = [0.1, 0.2, 0.15, 0.05]. None are >= 0.9.
        # So p_value should be 0.0.
        self.assertAlmostEqual(p_value, 0.0, places=2)
        self.assertAlmostEqual(obs_r2, 0.9, places=2)

    def test_run_permutation_test_integration(self):
        """Integration test for the full permutation test run."""
        # We need a model that actually fits the data to avoid random errors
        # Re-fit the model on the actual data extracted from features
        X = np.array([[row['feature1'], row['feature2']] for row in self.features_data[:3]])
        y = np.array([row['fidelity_loss'] for row in self.features_data[:3]])
        
        model = RandomForestRegressor(n_estimators=5, random_state=42)
        model.fit(X, y)
        
        import pickle
        with open(self.model_path, 'wb') as f:
            pickle.dump(model, f)

        results = run_permutation_test(
            features_path=self.features_path,
            split_config_path=self.split_config_path,
            model_path=self.model_path,
            output_path=self.output_path,
            n_permutations=10, # Small number for speed
            random_state=42
        )

        self.assertIn("p_value_permutation", results)
        self.assertIn("observed_r2", results)
        self.assertIn("permuted_r2_stats", results)
        self.assertTrue(0.0 <= results["p_value_permutation"] <= 1.0)
        self.assertTrue(os.path.exists(self.output_path))

    def test_run_permutation_test_ridge(self):
        """Test permutation test with Ridge regression model."""
        # Create Ridge model
        X = np.array([[row['feature1'], row['feature2']] for row in self.features_data[:3]])
        y = np.array([row['fidelity_loss'] for row in self.features_data[:3]])
        
        model = Ridge(alpha=1.0, random_state=42)
        model.fit(X, y)
        
        import pickle
        with open(self.model_path, 'wb') as f:
            pickle.dump(model, f)

        results = run_permutation_test(
            features_path=self.features_path,
            split_config_path=self.split_config_path,
            model_path=self.model_path,
            output_path=self.output_path,
            n_permutations=10,
            random_state=42
        )

        self.assertIn("p_value_permutation", results)

if __name__ == "__main__":
    unittest.main()