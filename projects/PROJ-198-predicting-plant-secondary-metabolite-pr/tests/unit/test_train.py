import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from modeling.train import (
    apply_pca, 
    train_models_loo, 
    train_models_5fold, 
    determine_cv_method,
    load_pca_features,
    ModelTrainingError
)

@pytest.fixture
def sample_data():
    """Create sample feature and target data."""
    np.random.seed(42)
    n_samples = 15
    n_features = 10
    
    X = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f'feature_{i}' for i in range(n_features)]
    )
    y = pd.Series(np.random.randn(n_samples), name='target')
    
    return X, y

@pytest.fixture
def sample_large_data():
    """Create larger sample data for 5-fold CV testing."""
    np.random.seed(42)
    n_samples = 25
    n_features = 10
    
    X = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f'feature_{i}' for i in range(n_features)]
    )
    y = pd.Series(np.random.randn(n_samples), name='target')
    
    return X, y

def test_determine_cv_method():
    """Test CV method selection logic."""
    assert determine_cv_method(10) == 'loo'
    assert determine_cv_method(19) == 'loo'
    assert determine_cv_method(20) == '5fold'
    assert determine_cv_method(50) == '5fold'

def test_apply_pca_creates_output(tmp_path):
    """Test that PCA creates output file and reduces dimensions."""
    np.random.seed(42)
    n_samples = 20
    n_features = 10
    
    X = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f'feature_{i}' for i in range(n_features)]
    )
    
    output_path = tmp_path / "pca_test.csv"
    result = apply_pca(X, n_components=3, output_path=str(output_path))
    
    assert result.shape[1] == 3
    assert result.shape[0] == n_samples
    assert output_path.exists()
    
    # Check column names
    assert all(col.startswith('PC') for col in result.columns)

def test_apply_pca_variance_threshold(tmp_path):
    """Test PCA with variance threshold."""
    np.random.seed(42)
    n_samples = 20
    n_features = 10
    
    X = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f'feature_{i}' for i in range(n_features)]
    )
    
    output_path = tmp_path / "pca_variance.csv"
    result = apply_pca(X, output_path=str(output_path))
    
    # Should keep enough components for 95% variance
    assert result.shape[1] <= n_features
    assert result.shape[0] == n_samples
    assert output_path.exists()

def test_train_models_loo(sample_data, tmp_path):
    """Test LOO training returns valid results."""
    X, y = sample_data
    output_path = tmp_path / "loo_results.json"
    
    results = train_models_loo(X, y, output_path=str(output_path))
    
    # Check all models trained
    assert 'RandomForest' in results
    assert 'ElasticNet' in results
    assert 'GradientBoosting' in results
    
    # Check metrics present
    for model_name in ['RandomForest', 'ElasticNet', 'GradientBoosting']:
        assert 'mean_r2' in results[model_name]
        assert 'std_r2' in results[model_name]
        assert results[model_name]['mean_r2'] is not None
    
    # Check output file created
    assert output_path.exists()

def test_train_models_loo_empty_data():
    """Test that empty data raises error."""
    X = pd.DataFrame()
    y = pd.Series()
    
    with pytest.raises(ModelTrainingError):
        train_models_loo(X, y)

def test_train_models_5fold(sample_large_data, tmp_path):
    """Test 5-fold training returns valid results."""
    X, y = sample_large_data
    output_path = tmp_path / "5fold_results.json"
    
    results = train_models_5fold(X, y, output_path=str(output_path))
    
    # Check all models trained
    assert 'RandomForest' in results
    assert 'ElasticNet' in results
    assert 'GradientBoosting' in results
    
    # Check metrics present
    for model_name in ['RandomForest', 'ElasticNet', 'GradientBoosting']:
        assert 'mean_r2' in results[model_name]
        assert 'std_r2' in results[model_name]
        assert results[model_name]['mean_r2'] is not None
    
    # Check output file created
    assert output_path.exists()

def test_train_models_5fold_cv_count(sample_large_data, tmp_path):
    """Test that 5-fold produces correct number of scores."""
    X, y = sample_large_data
    output_path = tmp_path / "5fold_test.json"
    
    results = train_models_5fold(X, y, n_splits=5, output_path=str(output_path))
    
    # Each model should have 5 R2 scores
    for model_name in ['RandomForest', 'ElasticNet', 'GradientBoosting']:
        assert len(results[model_name]['r2_scores']) == 5

def test_load_pca_features_missing_file(tmp_path):
    """Test loading non-existent file raises error."""
    non_existent = tmp_path / "missing.csv"
    
    with pytest.raises(FileNotFoundError):
        load_pca_features(str(non_existent))