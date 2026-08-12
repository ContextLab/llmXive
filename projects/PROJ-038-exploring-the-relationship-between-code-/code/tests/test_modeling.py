import pytest
import numpy as np
import pandas as pd
import tempfile
import os
from pathlib import Path
from src.modeling import train_logistic_regression, train_random_forest, prepare_features, load_features_csv

@pytest.fixture
def sample_data():
    """Create a sample dataset for testing."""
    np.random.seed(42)
    n_samples = 100
    data = {
        'cc': np.random.randint(1, 20, n_samples),
        'halstead': np.random.uniform(10, 100, n_samples),
        'loc': np.random.randint(10, 500, n_samples),
        'is_buggy': np.random.randint(0, 2, n_samples)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_csv(sample_data):
    """Create a temporary CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        sample_data.to_csv(f.name, index=False)
        yield f.name
    os.unlink(f.name)

def test_prepare_features(temp_csv):
    """Test that prepare_features correctly extracts X and y."""
    df = load_features_csv(temp_csv)
    X, y = prepare_features(df)
    
    assert X.shape == (100, 3)
    assert y.shape == (100,)
    assert X.dtype == np.float64
    assert y.dtype == np.int64

def test_logistic_regression_returns_results(temp_csv):
    """Test that logistic regression training returns valid results."""
    df = load_features_csv(temp_csv)
    X, y = prepare_features(df)
    
    model, results = train_logistic_regression(X, y, seed=42)
    
    assert 'roc_auc' in results
    assert 'f1' in results
    assert 'mean' in results['roc_auc']
    assert 'std' in results['roc_auc']
    assert isinstance(results['roc_auc']['mean'], float)
    assert 0 <= results['roc_auc']['mean'] <= 1

def test_random_forest_returns_results(temp_csv):
    """Test that random forest training returns valid results."""
    df = load_features_csv(temp_csv)
    X, y = prepare_features(df)
    
    model, results = train_random_forest(X, y, seed=42)
    
    assert 'roc_auc' in results
    assert 'f1' in results
    assert 'mean' in results['roc_auc']
    assert 'std' in results['roc_auc']
    assert isinstance(results['roc_auc']['mean'], float)
    assert 0 <= results['roc_auc']['mean'] <= 1

def test_aggregation_across_folds(temp_csv):
    """Test that aggregation correctly computes mean and std across folds."""
    df = load_features_csv(temp_csv)
    X, y = prepare_features(df)
    
    _, results = train_logistic_regression(X, y, seed=42)
    
    # Check that we have 50 scores (5 folds * 10 repeats)
    assert len(results['roc_auc']['scores']) == 50
    assert len(results['f1']['scores']) == 50
    
    # Verify mean and std are calculated correctly
    scores = np.array(results['roc_auc']['scores'])
    assert np.isclose(results['roc_auc']['mean'], np.mean(scores))
    assert np.isclose(results['roc_auc']['std'], np.std(scores))