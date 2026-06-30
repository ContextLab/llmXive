"""
Unit tests for the bootstrap analysis module.
"""
import os
import sys
import json
import tempfile
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

# Add the project root to the path to allow imports
# Assuming this test runs from the project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.bootstrap import (
    compute_correlation_statistic,
    run_bootstrap_analysis,
    load_correlation_data
)

@pytest.fixture
def sample_data():
    """Create a sample dataframe for testing."""
    np.random.seed(42)
    n = 100
    # Create a positive correlation
    x = np.random.normal(0, 1, n)
    y = 0.5 * x + np.random.normal(0, 0.5, n)
    
    df = pd.DataFrame({
        'participant_id': [f'P{i}' for i in range(n)],
        'meta_auc': x,
        'd_prime': y
    })
    return df

@pytest.fixture
def temp_csv(sample_data):
    """Create a temporary CSV file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_data.to_csv(f.name, index=False)
        yield f.name
    os.unlink(f.name)

def test_load_correlation_data(temp_csv, sample_data):
    """Test loading data from CSV."""
    df = load_correlation_data(temp_csv)
    assert len(df) == len(sample_data)
    assert 'meta_auc' in df.columns
    assert 'd_prime' in df.columns

def test_compute_correlation_statistic(sample_data):
    """Test the correlation statistic function."""
    data = sample_data[['meta_auc', 'd_prime']].to_numpy()
    indices = np.arange(len(data))
    
    r = compute_correlation_statistic(data, indices)
    
    # Verify it's a valid correlation
    assert -1.0 <= r <= 1.0
    # Verify it's close to the true correlation (approx 0.5)
    assert 0.3 < r < 0.7

def test_compute_correlation_constant_input():
    """Test handling of constant input (zero variance)."""
    data = np.array([[1.0, 2.0], [1.0, 2.0], [1.0, 2.0]])
    indices = np.array([0, 1, 2])
    
    r = compute_correlation_statistic(data, indices)
    assert r == 0.0

def test_run_bootstrap_analysis(sample_data):
    """Test the full bootstrap analysis."""
    results = run_bootstrap_analysis(sample_data, bootstrap_count=100, seed=42)
    
    assert 'correlation' in results
    assert 'ci_lower' in results
    assert 'ci_upper' in results
    assert 'bootstrap_count' in results
    assert 'reduced' in results
    
    assert results['bootstrap_count'] == 100
    assert results['reduced'] == False
    assert -1.0 <= results['correlation'] <= 1.0
    assert results['ci_lower'] <= results['correlation'] <= results['ci_upper']

def test_bootstrap_with_small_sample(sample_data):
    """Test bootstrap with a very small sample size."""
    small_data = sample_data.head(5)
    results = run_bootstrap_analysis(small_data, bootstrap_count=10, seed=42)
    
    assert results['bootstrap_count'] == 10
    assert -1.0 <= results['correlation'] <= 1.0

def test_missing_columns(sample_data):
    """Test loading data with missing required columns."""
    df = sample_data.drop(columns=['d_prime'])
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f.name, index=False)
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError) as exc_info:
            load_correlation_data(temp_path)
        assert "missing required columns" in str(exc_info.value)
    finally:
        os.unlink(temp_path)

def test_file_not_found():
    """Test loading non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_correlation_data("non_existent_file.csv")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
