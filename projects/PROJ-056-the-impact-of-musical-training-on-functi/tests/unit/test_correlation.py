"""
Unit tests for correlation analysis module.
"""
import os
import sys
import tempfile
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.correlation import (
    load_musicians_connectivity_data,
    compute_connectivity_strength,
    compute_correlation_with_training,
    calculate_correlation_ci,
    calculate_effect_size_cohen_d,
    process_correlation_analysis
)
from utils.memory_monitor import MemoryLimitExceeded


def test_compute_connectivity_strength():
    """Test connectivity strength computation."""
    # Create a simple 3x3 connectivity matrix
    # Upper triangle values: (0,1)=0.5, (0,2)=0.6, (1,2)=0.7
    mat = np.array([
        [0.0, 0.5, 0.6],
        [0.5, 0.0, 0.7],
        [0.6, 0.7, 0.0]
    ])
    matrices = np.array([mat])

    strengths = compute_connectivity_strength(matrices)

    # Expected: (0.5 + 0.6 + 0.7) / 3 = 0.6
    expected = 0.6
    assert np.abs(strengths[0] - expected) < 1e-6, f"Expected {expected}, got {strengths[0]}"


def test_compute_correlation_with_training_pearson():
    """Test Pearson correlation calculation."""
    # Create synthetic data with known correlation
    np.random.seed(42)
    x = np.array([1, 2, 3, 4, 5])  # years of training
    y = np.array([2, 4, 5, 4, 5])  # connectivity strength (positive trend)

    r, p = compute_correlation_with_training(y, x, method='pearson')

    assert r > 0, "Correlation should be positive"
    assert 0 <= p <= 1, "p-value should be between 0 and 1"
    assert np.abs(r) <= 1, "Correlation coefficient should be between -1 and 1"


def test_compute_correlation_with_training_spearman():
    """Test Spearman correlation calculation."""
    np.random.seed(42)
    x = np.array([1, 2, 3, 4, 5])
    y = np.array([2, 4, 5, 4, 5])

    r, p = compute_correlation_with_training(y, x, method='spearman')

    assert r > 0, "Correlation should be positive"
    assert 0 <= p <= 1, "p-value should be between 0 and 1"


def test_calculate_correlation_ci():
    """Test confidence interval calculation."""
    r = 0.5
    n = 30
    ci_lower, ci_upper = calculate_correlation_ci(r, n)

    assert ci_lower < r < ci_upper, "CI should contain r"
    assert ci_lower >= -1 and ci_upper <= 1, "CI bounds should be within [-1, 1]"


def test_calculate_effect_size_cohen_d():
    """Test Cohen's d effect size calculation."""
    np.random.seed(42)
    strengths = np.random.randn(30) * 0.5 + 0.5
    years = np.arange(1, 31)

    d = calculate_effect_size_cohen_d(strengths, years)

    # Effect size should be a reasonable value
    assert not np.isnan(d), "Effect size should not be NaN"
    assert np.isfinite(d), "Effect size should be finite"


def test_load_musicians_connectivity_data():
    """Test loading musicians only from connectivity data."""
    # Create temporary files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        conn_path = tmpdir / "connectivity_matrices.npy"
        subjects_path = tmpdir / "subjects_cleaned.csv"

        # Create synthetic connectivity matrices (5 subjects)
        matrices = np.random.randn(5, 3, 3)
        np.save(conn_path, matrices)

        # Create subject data with mixed groups
        subjects_df = pd.DataFrame({
            'subject_id': [f'sub{i}' for i in range(5)],
            'group': ['musician', 'musician', 'non_musician', 'musician', 'non_musician'],
            'years_of_training': [3, 2, 0, 5, 0]
        })
        subjects_df.to_csv(subjects_path, index=False)

        # Load and filter
        loaded_matrices, musicians_df = load_musicians_connectivity_data(conn_path, subjects_path)

        # Should only have musicians
        assert len(musicians_df) == 3, f"Expected 3 musicians, got {len(musicians_df)}"
        assert loaded_matrices.shape[0] == 3, f"Expected 3 matrices, got {loaded_matrices.shape[0]}"
        assert all(musicians_df['years_of_training'] >= 1), "All musicians should have >= 1 year training"


def test_process_correlation_analysis_integration():
    """Test full correlation analysis pipeline."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        conn_path = tmpdir / "connectivity_matrices.npy"
        subjects_path = tmpdir / "subjects_cleaned.csv"
        output_path = tmpdir / "correlation_results.csv"

        # Create synthetic connectivity matrices (10 subjects, 3 ROIs)
        np.random.seed(42)
        n_subjects = 10
        n_rois = 3
        matrices = np.random.randn(n_subjects, n_rois, n_rois) * 0.5
        np.save(conn_path, matrices)

        # Create subject data with musicians having varying training years
        subjects_data = {
            'subject_id': [f'sub{i}' for i in range(n_subjects)],
            'group': ['musician'] * n_subjects,
            'years_of_training': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        }
        subjects_df = pd.DataFrame(subjects_data)
        subjects_df.to_csv(subjects_path, index=False)

        # Run analysis
        result_df = process_correlation_analysis(
            connectivity_path=conn_path,
            subjects_path=subjects_path,
            output_path=output_path
        )

        # Verify output file exists
        assert output_path.exists(), "Output CSV should exist"

        # Verify columns
        expected_columns = ['connection_id', 'r_value', 'p_value', 'effect_size', 'ci_95', 'stability_flag']
        assert list(result_df.columns) == expected_columns, f"Expected columns {expected_columns}, got {list(result_df.columns)}"

        # Verify stability flag is either 'low' or 'high'
        assert result_df['stability_flag'].iloc[0] in ['low', 'high'], "Stability flag should be 'low' or 'high'"

        # Verify r_value is between -1 and 1
        assert -1 <= result_df['r_value'].iloc[0] <= 1, "r_value should be between -1 and 1"

        # Verify p_value is between 0 and 1
        assert 0 <= result_df['p_value'].iloc[0] <= 1, "p_value should be between 0 and 1"