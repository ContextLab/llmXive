"""
Tests for feature selection module.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Mock config for testing
class MockConfig:
    def __init__(self):
        self.data = {
            "split_dir": "data/processed",
            "selection_frequency_path": "artifacts/reports/selection_frequency.csv"
        }
    
    def get(self, key, default=None):
        return self.data.get(key, default)

@pytest.fixture
def sample_data():
    """Create sample feature matrix and target vector."""
    np.random.seed(42)
    n_samples = 100
    n_features = 20
    
    X = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f"feature_{i}" for i in range(n_features)]
    )
    y = pd.Series(np.random.randint(0, 2, n_samples), name="resistance")
    
    return X, y

@pytest.fixture
def temp_output_dir():
    """Create temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_run_lasso_selection(sample_data):
    """Test LASSO feature selection returns valid feature list."""
    from code.analysis.feature_selection import run_lasso_selection
    
    X, y = sample_data
    selected = run_lasso_selection(X, y, alpha=0.1)
    
    assert isinstance(selected, list)
    assert all(isinstance(f, str) for f in selected)
    assert all(f in X.columns for f in selected)

def test_run_rf_selection(sample_data):
    """Test Random Forest feature selection returns valid feature list."""
    from code.analysis.feature_selection import run_rf_selection
    
    X, y = sample_data
    selected = run_rf_selection(X, y, threshold=0.01)
    
    assert isinstance(selected, list)
    assert all(isinstance(f, str) for f in selected)
    assert all(f in X.columns for f in selected)

def test_run_sensitivity_sweep(sample_data):
    """Test sensitivity sweep produces correct output format."""
    from code.analysis.feature_selection import run_sensitivity_sweep
    
    X, y = sample_data
    thresholds = [0.01, 0.05]
    n_iterations = 2
    
    result_df = run_sensitivity_sweep(
        X=X, 
        y=y, 
        thresholds=thresholds, 
        n_iterations=n_iterations
    )
    
    # Check columns
    assert 'feature_id' in result_df.columns
    assert 'threshold' in result_df.columns
    assert 'frequency' in result_df.columns
    
    # Check frequencies are between 0 and 1
    assert all((result_df['frequency'] >= 0) & (result_df['frequency'] <= 1))
    
    # Check that we have results for each threshold
    for t in thresholds:
        subset = result_df[result_df['threshold'] == t]
        assert len(subset) > 0  # At least some features selected

def test_save_selection_frequency(sample_data, temp_output_dir):
    """Test saving selection frequency to CSV."""
    from code.analysis.feature_selection import run_sensitivity_sweep, save_selection_frequency
    
    X, y = sample_data
    result_df = run_sensitivity_sweep(X, y, thresholds=[0.01], n_iterations=2)
    
    output_path = Path(temp_output_dir) / "test_selection.csv"
    save_selection_frequency(result_df, str(output_path))
    
    assert output_path.exists()
    
    # Verify loaded data matches
    loaded_df = pd.read_csv(output_path)
    assert len(loaded_df) == len(result_df)
    assert list(loaded_df.columns) == list(result_df.columns)