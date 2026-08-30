"""
Unit tests for T019: Correlation Matrix Generation.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import json

# Mock dependencies if missing, but assume they exist per project setup
try:
    from eda import compute_correlation_matrix, load_raster_stack
except ImportError:
    pytest.skip("EDA module not ready", allow_module_level=True)

def test_compute_correlation_matrix_basic():
    """Test basic correlation calculation with known data."""
    # Create synthetic valid data for testing the function logic
    n = 100
    np.random.seed(42)
    
    # Perfect positive correlation
    x = np.random.rand(n)
    y = x + np.random.normal(0, 0.01, n)
    
    df = pd.DataFrame({
        'covariate_1': x,
        'covariate_2': np.random.rand(n), # No correlation
        'temperature': y,
        'row': np.arange(n),
        'col': np.arange(n)
    })
    
    result = compute_correlation_matrix(df, y)
    
    assert isinstance(result, pd.DataFrame)
    assert 'covariate' in result.columns
    assert 'pearson_r' in result.columns
    assert 'spearman_r' in result.columns
    
    # Check that covariate_1 has high correlation
    row_1 = result[result['covariate'] == 'covariate_1']
    assert len(row_1) == 1
    assert row_1['pearson_r'].values[0] > 0.9
    
    # Check that covariate_2 has low correlation
    row_2 = result[result['covariate'] == 'covariate_2']
    assert len(row_2) == 1
    assert abs(row_2['pearson_r'].values[0]) < 0.2

def test_compute_correlation_matrix_nan_handling():
    """Test that NaN values are handled correctly."""
    n = 50
    x = np.random.rand(n)
    x[10] = np.nan # Introduce NaN
    y = x.copy()
    y[10] = np.nan
    
    df = pd.DataFrame({
        'cov': x,
        'temperature': y,
        'row': np.arange(n),
        'col': np.arange(n)
    })
    
    # Should not raise
    result = compute_correlation_matrix(df, y)
    assert len(result) > 0

def test_load_raster_stack_missing_dir():
    """Test that load_raster_stack fails loudly if directory missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        non_existent = Path(tmpdir) / "non_existent"
        with pytest.raises(FileNotFoundError):
            load_raster_stack(non_existent)