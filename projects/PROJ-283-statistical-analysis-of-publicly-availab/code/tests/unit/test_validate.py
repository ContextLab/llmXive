"""
Unit tests for the model validation module (T029, T030).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json
from unittest.mock import patch, MagicMock

from src.models.validate import (
    load_model_results,
    load_processed_data,
    prepare_features_and_target,
    perform_kfold_cross_validation,
    calculate_cv_metrics,
    run_validation_pipeline
)

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    np.random.seed(42)
    n_samples = 100
    
    df = pd.DataFrame({
        'material_imbalance_move10': np.random.randn(n_samples),
        'avg_move_time_white': np.random.uniform(5, 30, n_samples),
        'avg_move_time_black': np.random.uniform(5, 30, n_samples),
        'white_rating': np.random.uniform(1200, 2000, n_samples),
        'black_rating': np.random.uniform(1200, 2000, n_samples),
        'outcome_deviation': np.random.uniform(-0.5, 0.5, n_samples)
    })
    
    return df

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_load_processed_data_parquet(temp_dir, sample_data):
    """Test loading parquet file."""
    file_path = temp_dir / "test_data.parquet"
    sample_data.to_parquet(file_path)
    
    loaded_df = load_processed_data(str(file_path))
    assert loaded_df is not None
    assert len(loaded_df) == len(sample_data)
    assert list(loaded_df.columns) == list(sample_data.columns)

def test_load_processed_data_csv(temp_dir, sample_data):
    """Test loading CSV file."""
    file_path = temp_dir / "test_data.csv"
    sample_data.to_csv(file_path, index=False)
    
    loaded_df = load_processed_data(str(file_path))
    assert loaded_df is not None
    assert len(loaded_df) == len(sample_data)

def test_load_processed_data_not_found(temp_dir):
    """Test loading non-existent file."""
    file_path = temp_dir / "nonexistent.parquet"
    loaded_df = load_processed_data(str(file_path))
    assert loaded_df is None

def test_prepare_features_and_target(sample_data):
    """Test feature and target preparation."""
    X, y = prepare_features_and_target(sample_data)
    
    assert isinstance(X, np.ndarray)
    assert isinstance(y, np.ndarray)
    assert X.ndim == 2
    assert y.ndim == 1
    assert len(X) == len(y)
    assert X.shape[1] <= 5  # Number of features

def test_prepare_features_and_target_missing_columns(sample_data):
    """Test feature preparation with missing columns."""
    df = sample_data.drop(columns=['material_imbalance_move10'])
    
    with pytest.raises(ValueError, match="No valid feature columns"):
        prepare_features_and_target(df)

def test_perform_kfold_cross_validation_ridge(sample_data):
    """Test K-fold CV for Ridge regression."""
    X, y = prepare_features_and_target(sample_data)
    
    cv_results = perform_kfold_cross_validation(X, y, model_type="Ridge", k=3)
    
    assert 'r2_scores' in cv_results
    assert 'mse_scores' in cv_results
    assert len(cv_results['r2_scores']) == 3
    assert len(cv_results['mse_scores']) == 3
    assert all(isinstance(score, float) for score in cv_results['r2_scores'])

def test_calculate_cv_metrics_success(sample_data):
    """Test CV metrics calculation when threshold is met."""
    X, y = prepare_features_and_target(sample_data)
    cv_results = perform_kfold_cross_validation(X, y, model_type="Ridge", k=5)
    
    metrics = calculate_cv_metrics(cv_results, model_type="Ridge")
    
    assert 'cv_summary' in metrics
    assert 'validation_status' in metrics
    assert metrics['validation_status']['passed'] is True
    assert 'mean_r2' in metrics['cv_summary']
    assert 'std_r2' in metrics['cv_summary']

def test_calculate_cv_metrics_threshold_failure(temp_dir):
    """Test CV metrics calculation when threshold is exceeded."""
    # Create data with high variance
    np.random.seed(42)
    n_samples = 50
    df = pd.DataFrame({
        'material_imbalance_move10': np.random.randn(n_samples) * 10,
        'outcome_deviation': np.random.uniform(-10, 10, n_samples)
    })
    
    X, y = prepare_features_and_target(df)
    cv_results = perform_kfold_cross_validation(X, y, model_type="Ridge", k=3)
    
    # Force high variance by manipulating scores
    cv_results['r2_scores'] = [0.1, 0.9, 0.2]  # High std dev
    
    with pytest.raises(ValueError, match="SC-003 Validation Failed"):
        calculate_cv_metrics(cv_results, model_type="Ridge")

def test_run_validation_pipeline(temp_dir, sample_data):
    """Test full validation pipeline."""
    # Save test data
    data_path = temp_dir / "test_games.parquet"
    sample_data.to_parquet(data_path)
    
    results = run_validation_pipeline(
        data_path=str(data_path),
        k=3,
        model_types=["Ridge"]
    )
    
    assert 'Ridge' in results
    assert 'cv_summary' in results['Ridge']
    assert 'validation_status' in results['Ridge']

def test_run_validation_pipeline_missing_data(temp_dir):
    """Test pipeline with missing data file."""
    with pytest.raises(FileNotFoundError):
        run_validation_pipeline(data_path="nonexistent.parquet")

def test_load_model_results_not_found(temp_dir):
    """Test loading non-existent model results."""
    file_path = temp_dir / "nonexistent.json"
    results = load_model_results(str(file_path))
    assert results is None

def test_load_model_results_valid(temp_dir):
    """Test loading valid model results."""
    file_path = temp_dir / "test_results.json"
    test_data = {
        "model_type": "Ridge",
        "coefficients": [0.1, 0.2],
        "r_squared": 0.85
    }
    
    with open(file_path, 'w') as f:
        json.dump(test_data, f)
    
    results = load_model_results(str(file_path))
    assert results is not None
    assert results['model_type'] == "Ridge"
    assert results['r_squared'] == 0.85