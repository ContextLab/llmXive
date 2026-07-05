"""
Unit tests for model utility functions, specifically permutation importance.

Task: T020 [P] [US2] Unit test `tests/unit/test_model_utils.py::test_permutation_importance_returns_correct_scores`
"""
import pytest
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
import sys
import os

# Add project root to path to allow imports from code/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Import the module under test (or the specific function if it existed)
# Since the task is to test the logic, we will implement the function `calculate_permutation_importance`
# in a local helper or import it if it were in `code/models/model_utils.py`.
# Given the API surface doesn't show `model_utils.py` yet, we will implement the logic
# inside the test file's scope or a small helper module to ensure the test is self-contained
# and runnable, while adhering to the requirement of "real code".

# However, the task implies testing an existing function. Since `code/models/model_utils.py`
# is not in the provided API surface, we must create it as part of this task to satisfy
# the "implement the task for real" constraint, then test it.

from code.models import model_utils

class TestPermutationImportance:
    """Tests for permutation importance calculation."""

    def test_permutation_importance_returns_correct_scores(self):
        """
        Test that permutation importance returns correct scores for a known dataset.
        
        We create a synthetic dataset where feature 0 is perfectly correlated with target,
        and feature 1 is noise. Permutation of feature 0 should result in a large 
        increase in error (high importance), while feature 1 should have near-zero importance.
        """
        # Setup: Create a deterministic dataset
        np.random.seed(42)
        n_samples = 1000
        
        # Feature 0: Strong signal
        X0 = np.random.rand(n_samples)
        # Feature 1: Noise
        X1 = np.random.rand(n_samples)
        
        # Target: Perfectly dependent on X0
        y = 2.0 * X0 + 0.0 * X1 + 0.01 * np.random.randn(n_samples)
        
        X = np.column_stack([X0, X1])
        feature_names = ['signal_feature', 'noise_feature']
        
        # Train a simple model
        model = RandomForestRegressor(n_estimators=10, max_depth=3, random_state=42)
        model.fit(X, y)
        
        # Call the function under test
        result = model_utils.calculate_permutation_importance(
            model, X, y, feature_names=feature_names, n_repeats=5, random_state=42
        )
        
        # Assertions
        assert isinstance(result, dict), "Result should be a dictionary"
        assert 'signal_feature' in result, "Result should contain 'signal_feature'"
        assert 'noise_feature' in result, "Result should contain 'noise_feature'"
        
        signal_importance = result['signal_feature']
        noise_importance = result['noise_feature']
        
        # The signal feature should have significantly higher importance than the noise feature
        # We use a loose threshold because of the randomness in permutation, but the signal
        # must be clearly positive and larger than noise.
        assert signal_importance > 0.1, f"Signal importance ({signal_importance}) should be > 0.1"
        assert noise_importance < 0.05, f"Noise importance ({noise_importance}) should be < 0.05"
        assert signal_importance > noise_importance, \
            f"Signal importance ({signal_importance}) must be greater than noise importance ({noise_importance})"

    def test_permutation_importance_handles_single_feature(self):
        """Test permutation importance with a single feature."""
        np.random.seed(42)
        X = np.random.rand(100, 1)
        y = X[:, 0] + 0.1 * np.random.randn(100)
        
        model = RandomForestRegressor(n_estimators=5, random_state=42)
        model.fit(X, y)
        
        result = model_utils.calculate_permutation_importance(
            model, X, y, feature_names=['single_feature'], n_repeats=3, random_state=42
        )
        
        assert 'single_feature' in result
        assert result['single_feature'] > 0  # Should have some positive importance
