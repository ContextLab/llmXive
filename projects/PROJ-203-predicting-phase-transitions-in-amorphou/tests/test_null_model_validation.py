"""
Tests for T022: Null Model & Permutation Test.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from models.null_model_validation import (
    calculate_mean_predictor_metrics,
    run_permutation_test,
    load_final_dataset
)
from config import reset_config, get_paths

@pytest.fixture
def sample_regression_data():
    """Create sample data for regression testing."""
    np.random.seed(42)
    n = 50
    X = np.random.randn(n, 3)
    y = 2 * X[:, 0] + 3 * X[:, 1] - X[:, 2] + np.random.randn(n) * 0.5
    return X, y

@pytest.fixture
def sample_classification_data():
    """Create sample data for classification testing."""
    np.random.seed(42)
    n = 50
    X = np.random.randn(n, 3)
    # Create a separable classification problem
    y = (X[:, 0] + X[:, 1] > 0).astype(int)
    return X, y

def test_mean_predictor_regression():
    """Test mean predictor metrics for regression."""
    y_true = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
    y_pred_mean = 30.0  # Mean of y_true
    
    result = calculate_mean_predictor_metrics(y_true, y_pred_mean, "regression")
    
    assert result["task"] == "regression"
    assert result["metric"] == "rmse"
    assert result["baseline_type"] == "mean_predictor"
    assert result["baseline_value"] == 30.0
    
    # RMSE should be std(y_true) since we predict the mean
    expected_rmse = np.std(y_true)
    assert abs(result["value"] - expected_rmse) < 1e-6

def test_mean_predictor_classification():
    """Test mean predictor metrics for classification."""
    y_true = np.array([0, 0, 0, 1, 1])  # 60% class 0, 40% class 1
    y_pred_mean = 0.4  # Mean of y_true (probability of class 1)
    
    result = calculate_mean_predictor_metrics(y_true, y_pred_mean, "classification")
    
    assert result["task"] == "classification"
    assert result["metric"] == "accuracy"
    assert result["baseline_type"] == "mean_predictor"
    assert result["baseline_value"] == 0.4
    
    # With threshold 0.5, all predictions become 0 (since 0.4 < 0.5)
    # Accuracy should be 60% (3 out of 5 correct)
    assert result["value"] == 0.6

def test_permutation_test_regression(sample_regression_data):
    """Test permutation test for regression."""
    X, y = sample_regression_data
    
    # Use a small number of iterations for testing
    result = run_permutation_test(X, y, "regression", n_iterations=50)
    
    assert result["task"] == "regression"
    assert "baseline_score" in result
    assert "p_value" in result
    assert "n_permutations" in result
    assert result["n_permutations"] == 50
    assert "significance" in result
    
    # P-value should be between 0 and 1
    assert 0 <= result["p_value"] <= 1

def test_permutation_test_classification(sample_classification_data):
    """Test permutation test for classification."""
    X, y = sample_classification_data
    
    # Use a small number of iterations for testing
    result = run_permutation_test(X, y, "classification", n_iterations=50)
    
    assert result["task"] == "classification"
    assert "baseline_score" in result
    assert "p_value" in result
    assert "n_permutations" in result
    assert result["n_permutations"] == 50
    assert "significance" in result
    
    # P-value should be between 0 and 1
    assert 0 <= result["p_value"] <= 1

def test_load_final_dataset_missing_file():
    """Test that load_final_dataset fails loudly when file is missing."""
    with patch('config.get_paths') as mock_paths:
        # Mock paths to return a non-existent file
        mock_paths.return_value = {
            "processed": Path("/nonexistent/path")
        }
        
        with pytest.raises(FileNotFoundError, match="final_dataset.parquet not found"):
            load_final_dataset()

def test_permutation_test_with_identical_labels():
    """Test permutation test when all labels are identical (edge case)."""
    np.random.seed(42)
    X = np.random.randn(20, 3)
    y = np.ones(20)  # All ones
    
    # This should handle the edge case without crashing
    result = run_permutation_test(X, y, "classification", n_iterations=10)
    
    assert result["task"] == "classification"
    assert "p_value" in result
    # P-value might be 0 or 1 in this degenerate case, but should be valid
    assert 0 <= result["p_value"] <= 1
