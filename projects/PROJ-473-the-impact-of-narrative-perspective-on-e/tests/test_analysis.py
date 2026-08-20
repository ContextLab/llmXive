import pytest
import json
import os
import pandas as pd
import numpy as np
from code.analysis import (
    run_regression_analysis,
    apply_bonferroni_correction,
    calculate_vif,
    generate_scatter_plot,
    run_analysis_pipeline
)

@pytest.fixture
def temp_dataset(tmp_path):
    """Create a temporary CSV dataset for testing."""
    data = {
        'story_id': [f's{i}' for i in range(20)],
        'perspective_score': np.random.uniform(0, 1, 20),
        'empathy_score': np.random.uniform(1, 5, 20),
        'moral_judgement_score': np.random.uniform(1, 5, 20)
    }
    df = pd.DataFrame(data)
    path = tmp_path / "test_dataset.csv"
    df.to_csv(path, index=False)
    return str(path)

@pytest.fixture
def synthetic_linear_data(tmp_path):
    """Create a dataset with a known linear relationship for regression recovery."""
    # y = 2x + 1 + noise
    np.random.seed(42)
    x = np.linspace(0, 10, 50)
    noise = np.random.normal(0, 0.5, 50)
    y = 2 * x + 1 + noise
    
    data = {
        'story_id': [f's{i}' for i in range(50)],
        'perspective_score': x,
        'moral_judgement_score': y
    }
    df = pd.DataFrame(data)
    path = tmp_path / "synthetic_linear.csv"
    df.to_csv(path, index=False)
    return str(path)

def test_regression_recovery(synthetic_linear_data):
    """Test that regression recovers the known slope (2.0) within tolerance."""
    results = run_regression_analysis(synthetic_linear_data)
    
    assert results['slope'] is not None
    assert abs(results['slope'] - 2.0) < 0.5  # Allow some tolerance due to noise
    assert results['intercept'] is not None
    assert abs(results['intercept'] - 1.0) < 0.5
    assert results['r_squared'] > 0.8  # Should be high for linear data
    assert results['p_value'] < 0.05  # Should be significant

def test_bonferroni_correction():
    """Test Bonferroni correction logic."""
    p_values = [0.01, 0.03, 0.05]
    corrected = apply_bonferroni_correction(p_values, num_tests=3)
    
    expected = [0.03, 0.09, 0.15]
    for c, e in zip(corrected, expected):
        assert abs(c - e) < 0.001
    
    # Test clamping at 1.0
    p_values_high = [0.5, 0.6]
    corrected_high = apply_bonferroni_correction(p_values_high, num_tests=3)
    assert corrected_high[0] == 1.0  # 1.5 -> 1.0
    assert corrected_high[1] == 1.0  # 1.8 -> 1.0

def test_vif_calculation(temp_dataset):
    """Test VIF calculation (should be 1.0 for single predictor)."""
    vif_results = calculate_vif(temp_dataset)
    
    assert 'perspective_score' in vif_results
    assert abs(vif_results['perspective_score'] - 1.0) < 0.01

def test_analysis_pipeline(temp_dataset):
    """Test full analysis pipeline produces expected keys."""
    results = run_analysis_pipeline(temp_dataset)
    
    required_keys = ['slope', 'intercept', 'p_value', 'r_squared', 'bonferroni_adjusted_p', 'sample_size', 'vif_warning']
    assert all(k in results for k in required_keys)
    
    # Check types
    assert isinstance(results['slope'], (float, type(None)))
    assert isinstance(results['intercept'], (float, type(None)))
    assert isinstance(results['p_value'], (float, type(None)))
    assert isinstance(results['r_squared'], (float, type(None)))
    assert isinstance(results['bonferroni_adjusted_p'], (float, type(None)))
    assert isinstance(results['sample_size'], int)
    assert isinstance(results['vif_warning'], bool)

def test_generate_scatter_plot(tmp_path, temp_dataset):
    """Test that scatter plot is generated at the correct path."""
    output_path = str(tmp_path / "test_plot.png")
    success = generate_scatter_plot(temp_dataset, output_path)
    
    assert success
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0

def test_insufficient_data(temp_dataset, tmp_path):
    """Test handling of insufficient data points."""
    # Create a dataset with only 1 point
    data = {
        'story_id': ['s1'],
        'perspective_score': [0.5],
        'moral_judgement_score': [3.0]
    }
    df = pd.DataFrame(data)
    path = tmp_path / "single_point.csv"
    df.to_csv(path, index=False)
    
    results = run_regression_analysis(str(path))
    
    assert results['slope'] is None
    assert results['intercept'] is None
    assert results['p_value'] is None
    assert results['sample_size'] == 1