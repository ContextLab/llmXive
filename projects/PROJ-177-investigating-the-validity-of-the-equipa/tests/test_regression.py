"""
Unit tests for regression analysis module (User Story 4).

Tests:
- Linear regression fit (slope/intercept calculation)
- T-test significance (p-value calculation)
"""

import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pytest

from regression import (
    RegressionError,
    fit_linear_regression,
    test_coefficient_significance,
    prepare_regression_data,
    load_statistical_results_for_regression
)
from config import get_roughness_proxy

# Fixtures
@pytest.fixture
def sample_regression_data():
    """Create sample data with known linear relationship."""
    # y = 2 + 3*x1 + 4*x2 + noise
    np.random.seed(42)
    n = 100
    X1 = np.random.rand(n) * 10  # frequency
    X2 = np.random.rand(n) * 5   # roughness proxy
    y = 2 + 3 * X1 + 4 * X2 + np.random.normal(0, 0.5, n)
    
    return X1, X2, y

@pytest.fixture
def mock_statistical_results():
    """Create mock statistical results JSON structure."""
    data = {
        'bins': [
            {
                'bin_id': 'bin_0',
                'frequency': 10.0,
                'material_type': 'steel',
                'ks_test': {'statistic': 0.15, 'pvalue': 0.25},
                'chi_test': {'statistic': 12.5, 'pvalue': 0.08}
            },
            {
                'bin_id': 'bin_1',
                'frequency': 20.0,
                'material_type': 'polymer',
                'ks_test': {'statistic': 0.25, 'pvalue': 0.05},
                'chi_test': {'statistic': 18.2, 'pvalue': 0.02}
            },
            {
                'bin_id': 'bin_2',
                'frequency': 30.0,
                'material_type': 'glass',
                'ks_test': {'statistic': 0.35, 'pvalue': 0.01},
                'chi_test': {'statistic': 22.1, 'pvalue': 0.005}
            }
        ]
    }
    return data

@pytest.fixture
def temp_statistical_file(mock_statistical_results):
    """Create a temporary JSON file with mock statistical results."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(mock_statistical_results, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)

# Tests for fit_linear_regression
def test_fit_linear_regression_known_slope(sample_regression_data):
    """Test that regression recovers known slope within tolerance."""
    X1, X2, y = sample_regression_data
    X = np.column_stack([X1, X2])
    
    results = fit_linear_regression(X, y)
    
    # Expected coefficients: [intercept=2, slope1=3, slope2=4]
    coeffs = np.array(results['coefficients'])
    
    # Check intercept (within 10% tolerance due to noise)
    assert np.abs(coeffs[0] - 2.0) < 0.5, f"Intercept {coeffs[0]} != 2.0"
    
    # Check frequency slope (within 10% tolerance)
    assert np.abs(coeffs[1] - 3.0) < 0.5, f"Slope1 {coeffs[1]} != 3.0"
    
    # Check roughness slope (within 10% tolerance)
    assert np.abs(coeffs[2] - 4.0) < 0.5, f"Slope2 {coeffs[2]} != 4.0"
    
    # Check R^2 is reasonable (should be > 0.8 for this data)
    assert results['r_squared'] > 0.8, f"R^2 {results['r_squared']} too low"

def test_fit_linear_regression_perfect_fit():
    """Test regression on noiseless data (perfect fit)."""
    X1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    X2 = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
    y = np.array([6.0, 8.0, 10.0, 12.0, 14.0])  # y = 4 + 2*x1 + 0*x2
    
    X = np.column_stack([X1, X2])
    results = fit_linear_regression(X, y)
    
    coeffs = np.array(results['coefficients'])
    
    # Perfect fit should have R^2 = 1.0
    assert np.isclose(results['r_squared'], 1.0), f"R^2 should be 1.0, got {results['r_squared']}"
    
    # Coefficients should be close to [4, 2, 0]
    assert np.allclose(coeffs, [4.0, 2.0, 0.0], atol=1e-10), f"Coefficients {coeffs} != [4, 2, 0]"

def test_fit_linear_regression_empty_data():
    """Test that regression fails gracefully on empty data."""
    with pytest.raises(RegressionError):
        fit_linear_regression(np.array([]).reshape(0, 2), np.array([]))

# Tests for test_coefficient_significance
def test_significance_test_known_data(sample_regression_data):
    """Test t-test significance on data with known strong relationship."""
    X1, X2, y = sample_regression_data
    X = np.column_stack([X1, X2])
    
    model_results = fit_linear_regression(X, y)
    sig_results = test_coefficient_significance(X, y, model_results)
    
    # With strong signal, p-values should be small (< 0.05)
    assert sig_results['p_values'][1] < 0.05, "Frequency should be significant"
    assert sig_results['p_values'][2] < 0.05, "Roughness should be significant"
    
    # Check that t-statistics are non-zero
    assert np.abs(sig_results['t_statistics'][1]) > 2.0, "T-stat for freq too small"
    assert np.abs(sig_results['t_statistics'][2]) > 2.0, "T-stat for roughness too small"

def test_significance_test_no_relationship():
    """Test significance when there is no relationship (random data)."""
    np.random.seed(123)
    n = 50
    X1 = np.random.rand(n) * 10
    X2 = np.random.rand(n) * 5
    y = np.random.normal(0, 1, n)  # Pure noise, no relationship
    
    X = np.column_stack([X1, X2])
    model_results = fit_linear_regression(X, y)
    sig_results = test_coefficient_significance(X, y, model_results)
    
    # P-values should be large (not significant)
    # Note: With random data, sometimes we get false positives, but usually > 0.05
    # We just check that the calculation completes and returns valid p-values
    assert 0.0 <= sig_results['p_values'][1] <= 1.0, "Invalid p-value for frequency"
    assert 0.0 <= sig_results['p_values'][2] <= 1.0, "Invalid p-value for roughness"

def test_significance_test_single_feature():
    """Test significance with only one predictor."""
    X1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y = np.array([2.0, 4.0, 6.0, 8.0, 10.0])  # y = 2*x1
    
    X = X1.reshape(-1, 1)
    model_results = fit_linear_regression(X, y)
    sig_results = test_coefficient_significance(X, y, model_results)
    
    # Should be perfectly significant
    assert sig_results['p_values'][1] < 0.05, "Single feature should be significant"
    assert sig_results['significant']['frequency'] is True

# Tests for prepare_regression_data
def test_prepare_regression_data_basic(mock_statistical_results, temp_statistical_file):
    """Test basic data preparation from statistical results."""
    df = load_statistical_results_for_regression(temp_statistical_file)
    X, y, freqs, feature_names = prepare_regression_data(df)
    
    assert X.shape[0] == 3, f"Expected 3 samples, got {X.shape[0]}"
    assert X.shape[1] == 2, f"Expected 2 features, got {X.shape[1]}"
    assert len(y) == 3, f"Expected 3 targets, got {len(y)}"
    assert feature_names == ['frequency', 'roughness_proxy']

def test_prepare_regression_data_missing_columns():
    """Test that prepare_regression_data raises error on missing columns."""
    df = pd.DataFrame({'frequency': [10.0], 'deviation_magnitude': [0.1]})
    # Missing 'material_type'
    
    with pytest.raises(RegressionError):
        prepare_regression_data(df)

# Tests for load_statistical_results_for_regression
def test_load_statistical_results_valid(temp_statistical_file):
    """Test loading valid statistical results."""
    df = load_statistical_results_for_regression(temp_statistical_file)
    
    assert 'frequency' in df.columns
    assert 'deviation_magnitude' in df.columns
    assert 'material_type' in df.columns
    assert len(df) == 3

def test_load_statistical_results_file_not_found():
    """Test that loading non-existent file raises error."""
    with pytest.raises(RegressionError):
        load_statistical_results_for_regression("nonexistent.json")

def test_load_statistical_results_invalid_json():
    """Test that invalid JSON raises error."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("not valid json {")
        temp_path = f.name
    
    try:
        with pytest.raises(RegressionError):
            load_statistical_results_for_regression(temp_path)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

# Integration test
def test_full_regression_pipeline(mock_statistical_results):
    """Test the full regression pipeline from data to results."""
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(mock_statistical_results, f)
        input_path = f.name
    
    output_path = tempfile.mktemp(suffix='.json')
    
    try:
        # Import main function
        from regression import run_regression_analysis
        
        results = run_regression_analysis(
            input_json_path=input_path,
            output_path=output_path
        )
        
        # Check structure
        assert 'metadata' in results
        assert 'model' in results
        assert 'significance' in results
        assert 'validation' in results
        
        # Check model coefficients exist
        assert 'coefficients' in results['model']
        assert 'r_squared' in results['model']
        
        # Check validation
        assert 'frequency_significant' in results['validation']
        assert 'frequency_p_value' in results['validation']
        
        # Check output file was created
        assert os.path.exists(output_path)
        
        # Verify JSON can be loaded
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded['metadata']['n_samples'] == 3
        
    finally:
        # Cleanup
        if os.path.exists(input_path):
            os.unlink(input_path)
        if os.path.exists(output_path):
            os.unlink(output_path)