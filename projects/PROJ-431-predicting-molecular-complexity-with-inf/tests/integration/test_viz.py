import os
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # Ensure non-interactive backend for tests

from viz import plot_entropy_vs_property, plot_all_correlations, compute_regression_metrics

@pytest.fixture
def sample_df():
    """Create a sample DataFrame with realistic entropy and property values."""
    np.random.seed(42)
    n = 100
    # Generate correlated data with some noise
    atom_entropy = np.random.uniform(1.0, 4.0, n)
    bond_entropy = np.random.uniform(1.5, 5.0, n)
    # logS roughly correlated with atom_entropy (negative correlation)
    logS = -0.5 * atom_entropy + np.random.normal(0, 0.5, n)
    # logP roughly correlated with bond_entropy (positive correlation)
    logP = 0.8 * bond_entropy + np.random.normal(0, 0.5, n)
    
    return pd.DataFrame({
        'atom_entropy': atom_entropy,
        'bond_entropy': bond_entropy,
        'logS': logS,
        'logP': logP
    })

@pytest.fixture
def temp_output_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_compute_regression_metrics():
    """Test regression metrics calculation."""
    x = np.array([1, 2, 3, 4, 5])
    y = np.array([2, 4, 5, 4, 5])
    
    metrics = compute_regression_metrics(x, y)
    
    assert 'slope' in metrics
    assert 'intercept' in metrics
    assert 'r_value' in metrics
    assert 'r_squared' in metrics
    assert not np.isnan(metrics['r_squared'])

def test_plot_entropy_vs_property_creates_file(sample_df, temp_output_dir):
    """Test that plot function creates a valid PNG file."""
    output_path = os.path.join(temp_output_dir, "test_plot.png")
    
    metrics = plot_entropy_vs_property(
        sample_df,
        entropy_col='atom_entropy',
        property_col='logS',
        output_path=output_path,
        title="Test Plot"
    )
    
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0
    assert 'r_squared' in metrics

def test_plot_all_correlations_generates_multiple_files(sample_df, temp_output_dir):
    """Test that plot_all_correlations generates all required plots."""
    metrics = plot_all_correlations(
        sample_df,
        output_dir=temp_output_dir,
        entropy_cols=['atom_entropy', 'bond_entropy'],
        property_cols=['logS', 'logP']
    )
    
    expected_plots = [
        'entropy_atom_entropy_vs_logS',
        'entropy_atom_entropy_vs_logP',
        'entropy_bond_entropy_vs_logS',
        'entropy_bond_entropy_vs_logP'
    ]
    
    for plot_name in expected_plots:
        assert plot_name in metrics
        expected_path = os.path.join(temp_output_dir, f"{plot_name}.png")
        assert os.path.exists(expected_path)
        assert os.path.getsize(expected_path) > 0

def test_plot_handles_nan_values(sample_df, temp_output_dir):
    """Test that plots handle NaN values gracefully."""
    # Inject NaNs
    df_with_nan = sample_df.copy()
    df_with_nan.loc[0, 'atom_entropy'] = np.nan
    df_with_nan.loc[1, 'logS'] = np.nan
    
    output_path = os.path.join(temp_output_dir, "test_nan.png")
    
    # Should not raise an error
    metrics = plot_entropy_vs_property(
        df_with_nan,
        entropy_col='atom_entropy',
        property_col='logS',
        output_path=output_path
    )
    
    assert os.path.exists(output_path)
    # Metrics should still be calculable on non-NaN data
    assert not np.isnan(metrics['r_squared']) or len(df_with_nan.dropna()) < 2