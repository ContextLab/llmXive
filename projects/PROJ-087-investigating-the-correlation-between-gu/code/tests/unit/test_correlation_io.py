"""
Unit tests for correlation I/O functions (T024).
"""
import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path

from src.correlation_io import save_correlation_results


@pytest.fixture
def sample_correlation_results():
    """Create a sample DataFrame with correlation results."""
    return pd.DataFrame({
        'diversity_metric': ['Shannon', 'Simpson', 'Observed_OTUs'],
        'sleep_metric': ['sleep_efficiency', 'sleep_duration_hours', 'sleep_efficiency'],
        'spearman_r': [0.35, -0.12, 0.05],
        'p_value': [0.001, 0.45, 0.82],
        'q_value': [0.003, 0.55, 0.90],
        'is_significant': [True, False, False],
        'is_moderate': [True, False, False],
        'is_meaningful': [True, False, False]
    })


def test_save_correlation_results_creates_file(sample_correlation_results):
    """Test that save_correlation_results creates a valid CSV file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'test_results.csv')
        result_path = save_correlation_results(sample_correlation_results, output_path)

        assert os.path.exists(result_path)
        assert result_path == output_path

        # Verify file contents
        loaded_df = pd.read_csv(result_path)
        assert len(loaded_df) == 3
        assert list(loaded_df.columns) == [
            'diversity_metric', 'sleep_metric', 'spearman_r',
            'p_value', 'q_value', 'is_significant', 'is_moderate', 'is_meaningful'
        ]
        assert loaded_df.iloc[0]['diversity_metric'] == 'Shannon'
        assert loaded_df.iloc[0]['spearman_r'] == 0.35


def test_save_correlation_results_empty_dataframe():
    """Test handling of empty DataFrame."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'empty_results.csv')
        empty_df = pd.DataFrame()
        result_path = save_correlation_results(empty_df, output_path)

        assert os.path.exists(result_path)
        loaded_df = pd.read_csv(result_path)
        # Should have columns but no rows
        assert len(loaded_df) == 0
        assert 'spearman_r' in loaded_df.columns


def test_save_correlation_results_creates_directory():
    """Test that save_correlation_results creates parent directories if needed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'nested', 'dir', 'test_results.csv')
        sample_df = pd.DataFrame({
            'diversity_metric': ['Shannon'],
            'sleep_metric': ['sleep_efficiency'],
            'spearman_r': [0.35],
            'p_value': [0.001],
            'q_value': [0.003],
            'is_significant': [True],
            'is_moderate': [True],
            'is_meaningful': [True]
        })

        result_path = save_correlation_results(sample_df, output_path)

        assert os.path.exists(result_path)
        assert os.path.isfile(result_path)


def test_save_correlation_results_data_integrity(sample_correlation_results):
    """Test that saved data matches original data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'integrity_test.csv')
        save_correlation_results(sample_correlation_results, output_path)

        loaded_df = pd.read_csv(output_path)

        # Check specific values
        assert loaded_df.iloc[0]['spearman_r'] == pytest.approx(0.35)
        assert loaded_df.iloc[0]['q_value'] == pytest.approx(0.003)
        assert loaded_df.iloc[0]['is_moderate'] == True
        assert loaded_df.iloc[1]['is_meaningful'] == False