import pytest
import numpy as np
import pandas as pd
import json
import os
import tempfile
from pathlib import Path

from classification import (
    load_features,
    train_and_validate,
    permutation_test,
    run_classification
)
from config import get_seed

@pytest.fixture
def sample_features_csv(tmp_path):
    """Create a sample features CSV file for testing."""
    # Create synthetic but realistic feature data
    np.random.seed(42)
    n_samples = 120
    n_features = 10
    
    # Generate features with some structure
    X = np.random.randn(n_samples, n_features)
    # Add some signal for class separation
    X[:60, :5] += 0.5
    X[60:, 5:] += 0.5
    
    # Labels: 0 for first 60, 1 for last 60
    y = np.array([0]*60 + [1]*60)
    
    # Create DataFrame
    feature_names = [f"feature_{i}" for i in range(n_features)]
    df = pd.DataFrame(X, columns=feature_names)
    df['label'] = y
    
    # Save to temp file
    csv_path = tmp_path / "features_matrix.csv"
    df.to_csv(csv_path, index=False)
    
    return str(csv_path)

def test_load_features(sample_features_csv):
    """Test loading features from CSV."""
    X, y = load_features(sample_features_csv)
    
    assert X.shape[0] == 120
    assert X.shape[1] == 10
    assert len(y) == 120
    assert set(np.unique(y)) == {0, 1}

def test_train_and_validate(sample_features_csv):
    """Test training and validation pipeline."""
    X, y = load_features(sample_features_csv)
    result = train_and_validate(X, y, n_folds=3)
    
    assert result.accuracy is not None
    assert result.precision is not None
    assert result.recall is not None
    assert result.cv_mean_accuracy is not None
    assert result.cv_std_accuracy is not None
    assert len(result.cv_scores) == 3
    assert 0 <= result.accuracy <= 1
    assert 0 <= result.precision <= 1
    assert 0 <= result.recall <= 1

def test_permutation_test(sample_features_csv):
    """Test permutation testing functionality."""
    X, y = load_features(sample_features_csv)
    
    # Use small number for faster testing
    result = permutation_test(X, y, n_permutations=50, n_folds=3)
    
    assert result.observed_accuracy is not None
    assert result.p_value is not None
    assert result.is_significant is not None
    assert result.n_permutations == 50
    assert len(result.null_distribution) == 50
    assert 0 <= result.p_value <= 1
    assert isinstance(result.is_significant, bool)

def test_run_classification(sample_features_csv, tmp_path):
    """Test full classification pipeline with output."""
    output_path = str(tmp_path / "classification_results.json")
    
    results = run_classification(
        features_path=sample_features_csv,
        output_path=output_path,
        n_permutations=50,
        n_folds=3
    )
    
    # Check output file exists
    assert os.path.exists(output_path)
    
    # Check results structure
    assert "classification" in results
    assert "permutation_test" in results
    assert "accuracy" in results["classification"]
    assert "p_value" in results["permutation_test"]
    
    # Check JSON file content
    with open(output_path, 'r') as f:
        saved_results = json.load(f)
    
    assert saved_results["classification"]["accuracy"] == results["classification"]["accuracy"]
    assert saved_results["permutation_test"]["p_value"] == results["permutation_test"]["p_value"]

def test_permutation_test_significance_detection():
    """Test that permutation test can detect significant results."""
    np.random.seed(42)
    n_samples = 100
    n_features = 5
    
    # Create data with clear separation
    X = np.random.randn(n_samples, n_features)
    X[:50, 0] += 2.0  # Strong signal in first feature for class 0
    X[50:, 0] -= 2.0  # Strong signal in first feature for class 1
    
    y = np.array([0]*50 + [1]*50)
    
    result = permutation_test(X, y, n_permutations=100, n_folds=5)
    
    # With clear signal, should be significant
    assert result.p_value < 0.05
    assert result.is_significant is True

def test_permutation_test_random_data():
    """Test that permutation test correctly identifies random data as non-significant."""
    np.random.seed(42)
    n_samples = 100
    n_features = 5
    
    # Create random data with no signal
    X = np.random.randn(n_samples, n_features)
    y = np.random.randint(0, 2, n_samples)
    
    result = permutation_test(X, y, n_permutations=100, n_folds=5)
    
    # With random data, p-value should be high (not significant)
    # Note: With only 100 permutations, there's variance, but typically > 0.05
    assert result.p_value > 0.05 or result.is_significant is False
