"""
Unit tests for the Sensitivity Analysis Report generation (T025).
"""
import os
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import pytest

# Import the module functions
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from generate_sensitivity_report import load_metrics_csv, aggregate_by_n

@pytest.fixture
def mock_csv_path(tmp_path):
    """Create a mock coverage_metrics.csv file."""
    csv_path = tmp_path / "coverage_metrics.csv"
    
    # Create mock data covering N=50, 100, 200
    data = {
        'phi': [0.5, 0.5, 0.5, 0.8, 0.8, 0.8],
        'n': [50, 100, 200, 50, 100, 200],
        'ordered_cov': [0.85, 0.88, 0.90, 0.75, 0.78, 0.80],
        'shuffled_cov': [0.94, 0.95, 0.95, 0.94, 0.95, 0.95],
        'diff': [-0.09, -0.07, -0.05, -0.19, -0.17, -0.15],
        'p_value': [0.01, 0.02, 0.03, 0.001, 0.002, 0.003],
        'ci_width_ratio': [1.1, 1.05, 1.02, 1.2, 1.15, 1.1],
        'bias_block': [0.02, 0.01, 0.005, 0.03, 0.025, 0.02]
    }
    
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    return csv_path

def test_load_metrics_csv_valid(mock_csv_path):
    """Test loading a valid CSV file."""
    df = load_metrics_csv(mock_csv_path)
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 6
    assert set(df.columns) == {'phi', 'n', 'ordered_cov', 'shuffled_cov', 'diff', 'p_value', 'ci_width_ratio', 'bias_block'}
    
    # Check specific values
    assert df['n'].unique().tolist() == [50, 100, 200]
    assert df[df['n'] == 50]['ordered_cov'].iloc[0] == 0.85

def test_load_metrics_csv_missing_file(tmp_path):
    """Test that loading a missing file raises FileNotFoundError."""
    missing_path = tmp_path / "nonexistent.csv"
    with pytest.raises(FileNotFoundError):
        load_metrics_csv(missing_path)

def test_load_metrics_csv_missing_columns(mock_csv_path):
    """Test that loading a CSV with missing columns raises ValueError."""
    # Create a CSV with missing columns
    bad_csv = mock_csv_path.parent / "bad.csv"
    bad_data = {'phi': [0.5], 'n': [50]} # Missing required columns
    pd.DataFrame(bad_data).to_csv(bad_csv, index=False)
    
    with pytest.raises(ValueError) as excinfo:
        load_metrics_csv(bad_csv)
    assert "Missing required columns" in str(excinfo.value)

def test_aggregate_by_n(mock_csv_path):
    """Test aggregation by sample size N."""
    df = load_metrics_csv(mock_csv_path)
    agg_df = aggregate_by_n(df)
    
    assert isinstance(agg_df, pd.DataFrame)
    assert len(agg_df) == 3 # Should have 3 rows for N=50, 100, 200
    assert list(agg_df['n']) == [50, 100, 200]
    
    # Check that aggregation worked (means should be computed)
    assert 'ordered_mean' in agg_df.columns
    assert 'shuffled_mean' in agg_df.columns
    assert 'diff_mean' in agg_df.columns
    
    # Verify a specific aggregation
    row_50 = agg_df[agg_df['n'] == 50].iloc[0]
    expected_ordered_mean = (0.85 + 0.75) / 2 # Average of phi=0.5 and phi=0.8 for N=50
    assert np.isclose(row_50['ordered_mean'], expected_ordered_mean)

def test_aggregate_by_n_empty_input(tmp_path):
    """Test aggregation with empty dataframe (edge case)."""
    csv_path = tmp_path / "empty.csv"
    cols = ['phi', 'n', 'ordered_cov', 'shuffled_cov', 'diff', 'p_value']
    pd.DataFrame(columns=cols).to_csv(csv_path, index=False)
    
    df = load_metrics_csv(csv_path)
    agg_df = aggregate_by_n(df)
    
    assert len(agg_df) == 0
    assert 'n' in agg_df.columns