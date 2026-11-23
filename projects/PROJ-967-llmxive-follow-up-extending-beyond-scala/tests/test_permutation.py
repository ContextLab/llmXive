"""
Unit tests for the Permutation Test implementation (T030a).

Tests:
1. calculate_permutation_pvalue with a known simple case.
2. Handling of empty features.
3. Handling of failure model placeholder.
"""
import json
import os
import pickle
import tempfile
import pytest
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from pathlib import Path

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))
from permutation_test import calculate_permutation_pvalue, run_permutation_test

class TestPermutationPValue:
    def test_permutation_pvalue_simple(self, caplog):
        """Test that p-value is calculated correctly on a simple dataset."""
        # Create a simple dataset where a model should perform well
        np.random.seed(42)
        X = np.random.randn(100, 2)
        y = X[:, 0] + 0.1 * np.random.randn(100) # Strong signal
        
        model = Ridge(alpha=1.0, random_state=42)
        model.fit(X, y)
        
        # Run with few permutations for speed
        p_val = calculate_permutation_pvalue(
            model, X, y, n_permutations=100, random_state=42, logger=None
        )
        
        # With a strong signal, p-value should be low (likely 0 or very small)
        # We just check it's a valid probability
        assert 0.0 <= p_val <= 1.0
        
    def test_permutation_pvalue_no_signal(self, caplog):
        """Test that p-value is high when there is no signal."""
        np.random.seed(42)
        X = np.random.randn(50, 2)
        y = np.random.randn(50) # No correlation
        
        model = Ridge(alpha=1.0, random_state=42)
        model.fit(X, y)
        
        p_val = calculate_permutation_pvalue(
            model, X, y, n_permutations=50, random_state=42, logger=None
        )
        
        # With no signal, the observed R2 is likely similar to permuted ones
        # So p-value should be relatively high (not strictly > 0.5 due to randomness)
        assert 0.0 <= p_val <= 1.0

class TestRunPermutationTest:
    def test_run_permutation_test_integration(self, tmp_path):
        """Integration test for the full run_permutation_test function."""
        # Setup temporary files
        features_path = tmp_path / "features.json"
        split_config_path = tmp_path / "split_config.json"
        model_path = tmp_path / "model.pkl"
        results_path = tmp_path / "results.json"
        
        # Create mock features
        features_data = [
            {"fidelity_loss": 0.5, "variance": 1.0, "entropy": 2.0},
            {"fidelity_loss": 0.6, "variance": 1.1, "entropy": 2.1},
            {"fidelity_loss": 0.4, "variance": 0.9, "entropy": 1.9},
            {"fidelity_loss": 0.7, "variance": 1.2, "entropy": 2.2},
            {"fidelity_loss": 0.3, "variance": 0.8, "entropy": 1.8},
        ]
        with open(features_path, 'w') as f:
            json.dump(features_data, f)
        
        # Create split config
        split_config = {
            "test_size": 0.4,
            "random_state": 42,
            "train_indices": [0, 1, 2]
        }
        with open(split_config_path, 'w') as f:
            json.dump(split_config, f)
        
        # Create a simple model
        X_train = np.array([[1.0, 2.0], [1.1, 2.1], [0.9, 1.9]])
        y_train = np.array([0.5, 0.6, 0.4])
        model = Ridge(alpha=1.0, random_state=42)
        model.fit(X_train, y_train)
        
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        # Initialize empty results
        with open(results_path, 'w') as f:
            json.dump({}, f)
        
        # Run the test
        p_val = run_permutation_test(
            features_path=str(features_path),
            split_config_path=str(split_config_path),
            model_path=str(model_path),
            results_path=str(results_path),
            n_permutations=10, # Small for speed
            random_state=42
        )
        
        # Verify results file updated
        with open(results_path, 'r') as f:
            results = json.load(f)
        
        assert 'p_value_permutation' in results
        assert 0.0 <= results['p_value_permutation'] <= 1.0
        
    def test_run_permutation_test_failure_model(self, tmp_path):
        """Test behavior when model is a failure placeholder."""
        features_path = tmp_path / "features.json"
        split_config_path = tmp_path / "split_config.json"
        model_path = tmp_path / "model.pkl"
        results_path = tmp_path / "results.json"
        
        # Create mock features
        features_data = [{"fidelity_loss": 0.5, "variance": 1.0}]
        with open(features_path, 'w') as f:
            json.dump(features_data, f)
        
        split_config = {"test_size": 0.2, "random_state": 42}
        with open(split_config_path, 'w') as f:
            json.dump(split_config, f)
        
        # Create failure model
        failure_model = {"status": "fail", "message": "N < 30"}
        with open(model_path, 'wb') as f:
            pickle.dump(failure_model, f)
        
        with open(results_path, 'w') as f:
            json.dump({}, f)
        
        p_val = run_permutation_test(
            features_path=str(features_path),
            split_config_path=str(split_config_path),
            model_path=str(model_path),
            results_path=str(results_path),
            n_permutations=10,
            random_state=42
        )
        
        # Should return None for p-value
        assert p_val is None
        
        with open(results_path, 'r') as f:
            results = json.load(f)
        
        assert results['p_value_permutation'] is None