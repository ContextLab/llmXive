"""
Unit tests for evaluation metrics and threshold checks (US2, T019).
Verifies metric calculations (R², MAE, RMSE) and SC-002 threshold checks.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Ensure project root is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.models.evaluator import (
    compute_metrics,
    check_sc002_threshold,
    evaluate_model_per_family,
    compute_per_family_metrics
)
from code.config import ensure_dirs

# Mock model for testing
class MockModel:
    def __init__(self, predictions):
        self._predictions = predictions

    def predict(self, X):
        return self._predictions

class MockTransformer:
    def inverse_transform(self, X):
        return X

class MockPipeline:
    def __init__(self, predictions):
        self.predictions = predictions
        self.steps = [
            ("transformer", MockTransformer()),
            ("model", MockModel(predictions))
        ]

    def predict(self, X):
        return self.predictions

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    np.random.seed(42)
    n_samples = 100
    
    # Create features
    X = pd.DataFrame({
        'temperature': np.random.uniform(300, 1000, n_samples),
        'strain_rate': np.random.uniform(0.01, 10, n_samples),
        'alloy_family': np.random.choice(['Al', 'Ti', 'Steel'], n_samples),
        'rolling_speed': np.random.uniform(0.5, 5.0, n_samples)
    })
    
    # Create targets (texture coefficients)
    y = pd.DataFrame({
        'ODF_{100}': np.random.uniform(0.5, 2.5, n_samples),
        'ODF_{110}': np.random.uniform(0.3, 2.0, n_samples),
        'ODF_{111}': np.random.uniform(0.4, 2.2, n_samples)
    })
    
    return X, y

@pytest.fixture
def mock_pipeline(sample_data):
    """Create a mock pipeline with known predictions."""
    X, y = sample_data
    # Create predictions with some error
    predictions = y.values + np.random.normal(0, 0.1, y.shape)
    return MockPipeline(predictions), y

def test_compute_metrics_basic(mock_pipeline):
    """Test basic metric computation."""
    pipeline, y_true = mock_pipeline
    
    metrics = compute_metrics(pipeline, y_true)
    
    assert 'r2' in metrics
    assert 'mae' in metrics
    assert 'rmse' in metrics
    assert metrics['r2'] <= 1.0  # R² cannot exceed 1
    assert metrics['mae'] >= 0   # MAE must be non-negative
    assert metrics['rmse'] >= 0  # RMSE must be non-negative

def test_compute_metrics_per_target(mock_pipeline):
    """Test metric computation per target variable."""
    pipeline, y_true = mock_pipeline
    
    metrics = compute_metrics(pipeline, y_true, per_target=True)
    
    assert isinstance(metrics, dict)
    assert 'ODF_{100}' in metrics
    assert 'ODF_{110}' in metrics
    assert 'ODF_{111}' in metrics
    
    for target in ['ODF_{100}', 'ODF_{110}', 'ODF_{111}']:
        assert 'r2' in metrics[target]
        assert 'mae' in metrics[target]
        assert 'rmse' in metrics[target]

def test_check_sc002_threshold_pass():
    """Test SC-002 threshold check when importance >= 0.10."""
    feature_importance = {
        'temperature': 0.15,
        'strain_rate': 0.12,
        'rolling_speed': 0.08
    }
    
    result = check_sc002_threshold(feature_importance, threshold=0.10)
    
    assert result['passed'] is True
    assert result['max_importance'] >= 0.10

def test_check_sc002_threshold_fail():
    """Test SC-002 threshold check when all importances < 0.10."""
    feature_importance = {
        'temperature': 0.05,
        'strain_rate': 0.03,
        'rolling_speed': 0.02
    }
    
    result = check_sc002_threshold(feature_importance, threshold=0.10)
    
    assert result['passed'] is False
    assert result['max_importance'] < 0.10

def test_check_sc002_threshold_edge_case():
    """Test SC-002 threshold check at exact boundary."""
    feature_importance = {
        'temperature': 0.10,
        'strain_rate': 0.05,
        'rolling_speed': 0.03
    }
    
    result = check_sc002_threshold(feature_importance, threshold=0.10)
    
    assert result['passed'] is True
    assert result['max_importance'] == 0.10

def test_evaluate_model_per_family(mock_pipeline):
    """Test per-family evaluation."""
    pipeline, y_true = mock_pipeline
    
    # Create sample data with family labels
    X = pd.DataFrame({
        'alloy_family': np.random.choice(['Al', 'Ti', 'Steel'], 100)
    })
    
    results = evaluate_model_per_family(pipeline, X, y_true)
    
    assert isinstance(results, dict)
    # Should have results for each family present in data
    families = X['alloy_family'].unique()
    for family in families:
        assert family in results
        assert 'r2' in results[family]
        assert 'mae' in results[family]
        assert 'rmse' in results[family]
        assert 'sample_count' in results[family]

def test_compute_per_family_metrics_with_thresholds(mock_pipeline):
    """Test per-family metrics with threshold checks."""
    pipeline, y_true = mock_pipeline
    
    X = pd.DataFrame({
        'alloy_family': np.random.choice(['Al', 'Ti', 'Steel'], 100)
    })
    
    results = compute_per_family_metrics(
        pipeline, X, y_true, 
        importance_threshold=0.10
    )
    
    assert isinstance(results, dict)
    for family, metrics in results.items():
        assert 'metrics' in metrics
        assert 'threshold_check' in metrics
        assert metrics['threshold_check']['family'] == family

def test_metric_consistency_across_families(mock_pipeline):
    """Test that metrics are consistent when computed per family vs overall."""
    pipeline, y_true = mock_pipeline
    
    # Overall metrics
    overall_metrics = compute_metrics(pipeline, y_true)
    
    # Create family labels
    X = pd.DataFrame({
        'alloy_family': ['Al'] * len(y_true)  # All same family
    })
    
    family_results = evaluate_model_per_family(pipeline, X, y_true)
    family_metrics = family_results['Al']
    
    # Should be very close (allowing for floating point)
    assert abs(overall_metrics['r2'] - family_metrics['r2']) < 1e-10
    assert abs(overall_metrics['mae'] - family_metrics['mae']) < 1e-10
    assert abs(overall_metrics['rmse'] - family_metrics['rmse']) < 1e-10

def test_empty_family_handling():
    """Test handling of empty families."""
    # Create empty dataframe
    y_empty = pd.DataFrame({
        'ODF_{100}': [],
        'ODF_{110}': [],
        'ODF_{111}': []
    })
    
    # This should not crash
    metrics = compute_metrics(MockModel(np.array([])), y_empty)
    
    # Metrics should be NaN or 0 for empty data
    assert np.isnan(metrics['r2']) or metrics['r2'] == 0
    assert np.isnan(metrics['mae']) or metrics['mae'] == 0
    assert np.isnan(metrics['rmse']) or metrics['rmse'] == 0

def test_single_sample_metrics():
    """Test metrics with single sample."""
    y_single = pd.DataFrame({
        'ODF_{100}': [1.5],
        'ODF_{110}': [1.2],
        'ODF_{111}': [1.8]
    })
    
    predictions = np.array([[1.5, 1.2, 1.8]])
    
    metrics = compute_metrics(MockModel(predictions), y_single)
    
    # Perfect prediction on single sample
    assert metrics['r2'] == 1.0
    assert metrics['mae'] == 0.0
    assert metrics['rmse'] == 0.0

def test_threshold_sensitivity():
    """Test different threshold values."""
    feature_importance = {
        'temperature': 0.15,
        'strain_rate': 0.12,
        'rolling_speed': 0.08
    }
    
    # Test various thresholds
    for threshold in [0.05, 0.10, 0.12, 0.15, 0.20]:
        result = check_sc002_threshold(feature_importance, threshold)
        
        if threshold <= 0.15:
            assert result['passed'] is True
        else:
            assert result['passed'] is False

def test_multiple_alloy_families_in_data():
    """Test evaluation with multiple alloy families."""
    np.random.seed(42)
    n_samples = 300
    
    X = pd.DataFrame({
        'alloy_family': np.random.choice(['Al', 'Ti', 'Steel'], n_samples)
    })
    
    y = pd.DataFrame({
        'ODF_{100}': np.random.uniform(0.5, 2.5, n_samples),
        'ODF_{110}': np.random.uniform(0.3, 2.0, n_samples),
        'ODF_{111}': np.random.uniform(0.4, 2.2, n_samples)
    })
    
    predictions = y.values + np.random.normal(0, 0.1, y.shape)
    pipeline = MockPipeline(predictions)
    
    results = evaluate_model_per_family(pipeline, X, y)
    
    # Should have results for all three families
    assert 'Al' in results
    assert 'Ti' in results
    assert 'Steel' in results
    
    # Each should have sample count
    for family in ['Al', 'Ti', 'Steel']:
        assert results[family]['sample_count'] > 0
        assert results[family]['sample_count'] < n_samples

def test_metric_values_within_expected_ranges():
    """Test that computed metrics fall within expected ranges."""
    np.random.seed(42)
    n_samples = 100
    
    y_true = pd.DataFrame({
        'ODF_{100}': np.random.uniform(0.5, 2.5, n_samples),
        'ODF_{110}': np.random.uniform(0.3, 2.0, n_samples),
        'ODF_{111}': np.random.uniform(0.4, 2.2, n_samples)
    })
    
    # Create predictions with controlled noise
    noise = np.random.normal(0, 0.2, y_true.shape)
    predictions = y_true.values + noise
    
    pipeline = MockPipeline(predictions)
    metrics = compute_metrics(pipeline, y_true)
    
    # R² should be between -1 and 1
    assert -1 <= metrics['r2'] <= 1
    
    # MAE and RMSE should be non-negative
    assert metrics['mae'] >= 0
    assert metrics['rmse'] >= 0
    
    # RMSE should be >= MAE (mathematical property)
    assert metrics['rmse'] >= metrics['mae']

def test_per_target_metrics_consistency():
    """Test that per-target metrics are consistent with overall metrics."""
    np.random.seed(42)
    n_samples = 100
    
    y_true = pd.DataFrame({
        'ODF_{100}': np.random.uniform(0.5, 2.5, n_samples),
        'ODF_{110}': np.random.uniform(0.3, 2.0, n_samples),
        'ODF_{111}': np.random.uniform(0.4, 2.2, n_samples)
    })
    
    predictions = y_true.values + np.random.normal(0, 0.1, y_true.shape)
    pipeline = MockPipeline(predictions)
    
    # Get per-target metrics
    per_target = compute_metrics(pipeline, y_true, per_target=True)
    
    # Get overall metrics
    overall = compute_metrics(pipeline, y_true)
    
    # Overall metrics should be averages of per-target metrics
    for metric_name in ['r2', 'mae', 'rmse']:
        per_target_avg = np.mean([per_target[target][metric_name] 
                                for target in y_true.columns])
        # Allow small floating point differences
        assert abs(per_target_avg - overall[metric_name]) < 1e-6

def test_sc002_with_empty_importance():
    """Test SC-002 check with empty feature importance dict."""
    result = check_sc002_threshold({}, threshold=0.10)
    
    assert result['passed'] is False
    assert result['max_importance'] == 0.0
    assert 'No features found' in result.get('message', '')

def test_sc002_with_single_feature():
    """Test SC-002 check with single feature."""
    feature_importance = {'temperature': 0.15}
    
    result = check_sc002_threshold(feature_importance, threshold=0.10)
    
    assert result['passed'] is True
    assert result['max_importance'] == 0.15
    assert result['max_feature'] == 'temperature'

def test_evaluate_model_with_missing_families():
    """Test evaluation when some families are missing from data."""
    np.random.seed(42)
    n_samples = 100
    
    # Only Al and Ti, no Steel
    X = pd.DataFrame({
        'alloy_family': np.random.choice(['Al', 'Ti'], n_samples)
    })
    
    y = pd.DataFrame({
        'ODF_{100}': np.random.uniform(0.5, 2.5, n_samples),
        'ODF_{110}': np.random.uniform(0.3, 2.0, n_samples),
        'ODF_{111}': np.random.uniform(0.4, 2.2, n_samples)
    })
    
    predictions = y.values + np.random.normal(0, 0.1, y.shape)
    pipeline = MockPipeline(predictions)
    
    results = evaluate_model_per_family(pipeline, X, y)
    
    # Should only have Al and Ti, not Steel
    assert 'Al' in results
    assert 'Ti' in results
    assert 'Steel' not in results

def test_threshold_check_with_multiple_features():
    """Test threshold check with many features."""
    feature_importance = {
        f'feature_{i}': np.random.uniform(0.01, 0.20) 
        for i in range(20)
    }
    
    # Ensure at least one feature passes
    feature_importance['strong_feature'] = 0.15
    
    result = check_sc002_threshold(feature_importance, threshold=0.10)
    
    assert result['passed'] is True
    assert result['max_feature'] == 'strong_feature'
    assert result['max_importance'] == 0.15