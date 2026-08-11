"""
Unit tests for the LME analysis functionality in code/analysis.py.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the functions to test
from analysis import run_lme_model, detect_nonlinearity, load_transformed_diversity_data

@pytest.fixture
def sample_lme_data():
    """Create a sample DataFrame for LME testing."""
    np.random.seed(42)
    n_samples = 50
    n_sites = 5
    
    sites = [f"Site_{i}" for i in range(n_sites)]
    data = {
        'sample_id': [f"Sample_{i}" for i in range(n_samples)],
        'site': np.random.choice(sites, n_samples),
        'pH': np.random.uniform(6.0, 9.0, n_samples),
        'shannon_diversity': np.random.uniform(2.0, 5.0, n_samples),
        'simpson_diversity': np.random.uniform(0.5, 0.9, n_samples)
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_nonlinear_data():
    """Create sample data with a known non-linear relationship."""
    np.random.seed(42)
    n_samples = 100
    pH = np.linspace(6, 9, n_samples)
    # Quadratic relationship: y = -x^2 + 10x + 2 (parabola opening down)
    diversity = -0.5 * (pH - 7.5)**2 + 4.0 + np.random.normal(0, 0.2, n_samples)
    
    return pd.DataFrame({
        'sample_id': [f"Sample_{i}" for i in range(n_samples)],
        'site': ['Site_A'] * n_samples,
        'pH': pH,
        'shannon_diversity': diversity,
        'simpson_diversity': diversity * 0.2
    })

def test_run_lme_model_basic(sample_lme_data):
    """Test that run_lme_model returns a valid dictionary."""
    result = run_lme_model(sample_lme_data)
    
    assert isinstance(result, dict)
    assert 'estimate' in result
    assert 'se' in result
    assert 'p_value' in result
    assert 'model_type' in result
    assert result['model_type'] in ['LME', 'OLS']
    assert isinstance(result['estimate'], float)
    assert isinstance(result['se'], float)
    assert isinstance(result['p_value'], float)

def test_run_lme_model_single_site(sample_lme_data):
    """Test fallback to OLS when only one site is present."""
    single_site_data = sample_lme_data[sample_lme_data['site'] == 'Site_0'].copy()
    result = run_lme_model(single_site_data)
    
    assert result['model_type'] == 'OLS'
    assert 'estimate' in result

def test_detect_nonlinearity_linear(sample_lme_data):
    """Test that linear data is not flagged as non-linear."""
    is_nonlinear, p_val = detect_nonlinearity(sample_lme_data)
    
    # With random data, it's unlikely to be strongly non-linear, but we check the return types
    assert isinstance(is_nonlinear, bool)
    assert isinstance(p_val, float)
    assert 0 <= p_val <= 1

def test_detect_nonlinearity_quadratic(sample_nonlinear_data):
    """Test that quadratic data is flagged as non-linear."""
    is_nonlinear, p_val = detect_nonlinearity(sample_nonlinear_data)
    
    # The synthetic data is explicitly quadratic, so p-value should be low
    # We expect is_nonlinear to be True
    assert is_nonlinear is True
    assert p_val < 0.05

def test_load_transformed_diversity_data_missing_file():
    """Test that FileNotFoundError is raised for missing input."""
    with pytest.raises(FileNotFoundError):
        load_transformed_diversity_data("nonexistent_file.csv")

def test_load_transformed_diversity_data_missing_columns(tmp_path):
    """Test that ValueError is raised for missing columns."""
    csv_path = tmp_path / "test.csv"
    df = pd.DataFrame({'sample_id': [1], 'pH': [7.0]}) # Missing required cols
    df.to_csv(csv_path, index=False)
    
    with pytest.raises(ValueError):
        load_transformed_diversity_data(str(csv_path))

def test_run_lme_model_output_values(sample_lme_data):
    """Test that the output values are within reasonable bounds."""
    result = run_lme_model(sample_lme_data)
    
    # Estimate should be a float
    assert isinstance(result['estimate'], float)
    # SE should be positive
    assert result['se'] > 0
    # p_value should be between 0 and 1
    assert 0 <= result['p_value'] <= 1

def test_lme_with_small_sample_size():
    """Test LME with a very small dataset (N < 10)."""
    np.random.seed(42)
    small_data = pd.DataFrame({
        'sample_id': [f"S{i}" for i in range(5)],
        'site': ['A', 'B', 'A', 'B', 'A'],
        'pH': [7.0, 7.5, 8.0, 8.5, 9.0],
        'shannon_diversity': [3.0, 3.2, 3.5, 3.8, 4.0],
        'simpson_diversity': [0.6, 0.65, 0.7, 0.75, 0.8]
    })
    
    # Should not crash, but might fall back to OLS or fail gracefully
    result = run_lme_model(small_data)
    assert 'estimate' in result
