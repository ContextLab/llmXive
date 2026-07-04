"""
Tests for drift_analysis module.
"""
import pytest
import tempfile
import csv
from pathlib import Path
import numpy as np
import pandas as pd

# Ensure code path is available
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from code.drift_analysis import (
    calculate_spearman_correlation,
    compute_pairwise_drift,
    save_drift_metrics,
    load_importance_profiles
)


@pytest.fixture
def sample_profiles_df():
    """Create a sample importance profiles DataFrame."""
    data = {
        'window_id': [1, 1, 1, 1, 2, 2, 2, 2],
        'feature': ['A', 'B', 'C', 'D', 'A', 'B', 'C', 'D'],
        'importance_score': [0.5, 0.3, 0.15, 0.05, 0.4, 0.35, 0.15, 0.1]
    }
    return pd.DataFrame(data)


@pytest.fixture
def temp_profiles_file(sample_profiles_df):
    """Create a temporary CSV file with sample profiles."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_profiles_df.to_csv(f, index=False)
        temp_path = Path(f.name)
    yield temp_path
    temp_path.unlink()


def test_load_importance_profiles(temp_profiles_file):
    """Test loading importance profiles from CSV."""
    df = load_importance_profiles(temp_profiles_file)
    assert len(df) == 8
    assert 'window_id' in df.columns
    assert 'feature' in df.columns
    assert 'importance_score' in df.columns


def test_load_importance_profiles_missing_file():
    """Test error handling for missing file."""
    with pytest.raises(FileNotFoundError):
        load_importance_profiles(Path("nonexistent.csv"))


def test_calculate_spearman_correlation():
    """Test Spearman correlation calculation."""
    idx = ['A', 'B', 'C', 'D']
    vec_t = pd.Series([0.5, 0.3, 0.15, 0.05], index=idx)
    vec_t1 = pd.Series([0.4, 0.35, 0.15, 0.1], index=idx)

    rho, p_value = calculate_spearman_correlation(vec_t, vec_t1)

    assert isinstance(rho, float)
    assert isinstance(p_value, float)
    assert -1.0 <= rho <= 1.0
    assert 0.0 <= p_value <= 1.0
    # Expected: positive correlation (similar rankings)
    assert rho > 0


def test_calculate_spearman_correlation_constant_vector():
    """Test handling of constant importance vectors."""
    idx = ['A', 'B', 'C']
    vec_t = pd.Series([0.33, 0.33, 0.33], index=idx)
    vec_t1 = pd.Series([0.5, 0.3, 0.2], index=idx)

    rho, p_value = calculate_spearman_correlation(vec_t, vec_t1)

    assert np.isnan(rho)
    assert np.isnan(p_value)


def test_calculate_spearman_correlation_insufficient_features():
    """Test handling of less than 2 common features."""
    idx1 = ['A', 'B']
    idx2 = ['C', 'D']
    vec_t = pd.Series([0.5, 0.5], index=idx1)
    vec_t1 = pd.Series([0.5, 0.5], index=idx2)

    rho, p_value = calculate_spearman_correlation(vec_t, vec_t1)

    assert np.isnan(rho)
    assert np.isnan(p_value)


def test_compute_pairwise_drift(sample_profiles_df):
    """Test pairwise drift computation."""
    results = compute_pairwise_drift(sample_profiles_df)

    assert len(results) == 1  # Only one transition: 1 -> 2
    result = results[0]

    assert result['window_t'] == 1
    assert result['window_t_plus_1'] == 2
    assert 'rho' in result
    assert 'p_value' in result
    assert isinstance(result['rho'], float)


def test_compute_pairwise_drift_single_window(sample_profiles_df):
    """Test handling of single window (no transitions)."""
    single_window = sample_profiles_df[sample_profiles_df['window_id'] == 1]
    results = compute_pairwise_drift(single_window)

    assert len(results) == 0


def test_save_drift_metrics():
    """Test saving drift metrics to CSV."""
    results = [
        {'window_t': 1, 'window_t_plus_1': 2, 'rho': 0.85, 'p_value': 0.02},
        {'window_t': 2, 'window_t_plus_1': 3, 'rho': 0.72, 'p_value': 0.05}
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        output_path = Path(f.name)

    save_drift_metrics(results, output_path)

    assert output_path.exists()
    df = pd.read_csv(output_path)
    assert len(df) == 2
    assert list(df.columns) == ['window_t', 'window_t_plus_1', 'rho', 'p_value']

    output_path.unlink()


def test_save_drift_metrics_empty():
    """Test saving empty drift metrics."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        output_path = Path(f.name)

    save_drift_metrics([], output_path)

    assert output_path.exists()
    df = pd.read_csv(output_path)
    assert len(df) == 0
    assert list(df.columns) == ['window_t', 'window_t_plus_1', 'rho', 'p_value']

    output_path.unlink()