import pytest
import json
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add code to path if running from root
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from modeling.evaluate import compute_permutation_importance

def test_compute_permutation_importance_structure():
    """Test that the output structure matches the specification."""
    # Create dummy data
    n_samples, n_features = 100, 20
    X = np.random.rand(n_samples, n_features)
    y = np.random.rand(n_samples)
    
    # Create a simple mock model that has a predict method
    class MockRF:
        def predict(self, X):
            return np.ones(X.shape[0])
        
        def score(self, X, y):
            return 0.5

    mock_model = MockRF()
    
    # Run function
    result = compute_permutation_importance(mock_model, X, y, n_repeats=5, random_seed=42)
    
    # Assertions
    assert isinstance(result, list), "Result must be a list"
    assert len(result) == n_features, f"Result length must match number of features ({n_features})"
    
    for item in result:
        assert isinstance(item, dict), "Each item must be a dict"
        assert "feature_index" in item, "Missing 'feature_index' key"
        assert "importance_score" in item, "Missing 'importance_score' key"
        assert isinstance(item["feature_index"], int), "feature_index must be int"
        assert isinstance(item["importance_score"], float), "importance_score must be float"
        
    # Check indices are unique and cover range
    indices = [item["feature_index"] for item in result]
    assert sorted(indices) == list(range(n_features)), "Indices must cover 0 to n_features-1"

def test_permutation_importance_deterministic():
    """Test that results are deterministic with fixed seed."""
    n_samples, n_features = 50, 10
    X = np.random.rand(n_samples, n_features)
    y = np.random.rand(n_samples)
    
    class MockRF:
        def predict(self, X):
            return np.ones(X.shape[0])
        def score(self, X, y):
            return 0.5

    mock_model = MockRF()
    
    result1 = compute_permutation_importance(mock_model, X, y, n_repeats=5, random_seed=123)
    result2 = compute_permutation_importance(mock_model, X, y, n_repeats=5, random_seed=123)
    
    for r1, r2 in zip(result1, result2):
        assert r1["feature_index"] == r2["feature_index"]
        assert r1["importance_score"] == r2["importance_score"]