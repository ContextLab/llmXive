import pytest
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from code.model_training import train_models, apply_log_transformation

@pytest.fixture
def sample_data():
    """Create a small sample dataset for testing."""
    np.random.seed(42)
    n_samples = 100
    data = {
        'feature1': np.random.randn(n_samples),
        'feature2': np.random.randn(n_samples),
        'feature3': np.random.randn(n_samples),
        'conductivity': np.random.randn(n_samples) * 2 + 5  # Some target values
    }
    return pd.DataFrame(data)

def test_train_models_returns_metrics(sample_data):
    """Test that train_models returns expected metrics structure."""
    feature_cols = ['feature1', 'feature2', 'feature3']
    target_col = 'conductivity'
    
    metrics, rf_model, gb_model = train_models(
        df=sample_data,
        feature_cols=feature_cols,
        target_col=target_col,
        log_transform=False
    )
    
    assert isinstance(metrics, dict)
    assert 'rf_cv_r2_mean' in metrics
    assert 'rf_cv_r2_std' in metrics
    assert 'gb_cv_r2_mean' in metrics
    assert 'gb_cv_r2_std' in metrics
    assert 'rf_cv_scores' in metrics
    assert 'gb_cv_scores' in metrics
    
    assert isinstance(rf_model, RandomForestRegressor)
    assert isinstance(gb_model, GradientBoostingRegressor)
    
    # Check that CV scores are lists of floats
    assert len(metrics['rf_cv_scores']) == 5
    assert len(metrics['gb_cv_scores']) == 5
    assert all(isinstance(s, float) for s in metrics['rf_cv_scores'])
    assert all(isinstance(s, float) for s in metrics['gb_cv_scores'])

def test_train_models_with_log_transform(sample_data):
    """Test that log transformation is applied correctly."""
    feature_cols = ['feature1', 'feature2', 'feature3']
    target_col = 'conductivity'
    
    metrics, rf_model, gb_model = train_models(
        df=sample_data,
        feature_cols=feature_cols,
        target_col=target_col,
        log_transform=True
    )
    
    # Should still return valid metrics
    assert metrics['rf_cv_r2_mean'] is not None
    assert metrics['gb_cv_r2_mean'] is not None

def test_cross_validation_scores_consistency(sample_data):
    """Test that CV scores are consistent across runs (with fixed seed)."""
    feature_cols = ['feature1', 'feature2', 'feature3']
    target_col = 'conductivity'
    
    metrics1, _, _ = train_models(sample_data, feature_cols, target_col, log_transform=False)
    metrics2, _, _ = train_models(sample_data, feature_cols, target_col, log_transform=False)
    
    # With fixed SEED, results should be identical
    np.testing.assert_array_almost_equal(
        metrics1['rf_cv_scores'], 
        metrics2['rf_cv_scores']
    )
    np.testing.assert_array_almost_equal(
        metrics1['gb_cv_scores'], 
        metrics2['gb_cv_scores']
    )

def test_log_transform_target():
    """Test that np.log(input_values) matches expected_output for a known array."""
    input_values = np.array([1.0, np.e, np.e**2, np.e**3])
    expected_output = np.array([0.0, 1.0, 2.0, 3.0])
    
    result = apply_log_transformation(input_values)
    
    np.testing.assert_array_almost_equal(result, expected_output)
    
    # Test with pandas Series
    series_input = pd.Series([1.0, np.e, np.e**2])
    series_result = apply_log_transformation(series_input)
    np.testing.assert_array_almost_equal(series_result.values, [0.0, 1.0, 2.0])
    
    # Test that log of non-positive values raises or handles appropriately
    # (depending on implementation, this might raise a warning or return nan)
    negative_input = np.array([-1.0, 0.0, 1.0])
    negative_result = apply_log_transformation(negative_input)
    assert np.isnan(negative_result[0])  # log(-1) is nan
    assert np.isnan(negative_result[1])  # log(0) is -inf (treated as nan in comparison)
    assert np.isclose(negative_result[2], 0.0)