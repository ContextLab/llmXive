import pytest
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from src.correlation import (
    calculate_spearman_correlation,
    apply_benjamini_hochberg,
    flag_correlations,
    handle_no_significant_associations,
    run_correlation_analysis
)
import tempfile
import os
from pathlib import Path

@pytest.fixture
def sample_diversity_df():
    """Sample diversity DataFrame for testing."""
    return pd.DataFrame({
        'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
        'shannon': [3.2, 3.5, 2.8, 3.1, 3.4],
        'simpson': [0.85, 0.88, 0.75, 0.82, 0.87],
        'observed_otus': [120, 135, 98, 115, 130]
    })

@pytest.fixture
def sample_sleep_df():
    """Sample sleep DataFrame for testing."""
    return pd.DataFrame({
        'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
        'sleep_efficiency': [0.85, 0.90, 0.70, 0.82, 0.88],
        'sleep_duration_hours': [7.5, 8.0, 6.0, 7.2, 7.8]
    })

def test_spearman_correlation_calculation(sample_diversity_df, sample_sleep_df):
    """Test that Spearman correlation is calculated correctly."""
    result = calculate_spearman_correlation(sample_diversity_df, sample_sleep_df)

    assert not result.empty
    assert 'r' in result.columns
    assert 'p' in result.columns
    assert 'n_samples' in result.columns
    assert len(result) == 6  # 3 diversity x 2 sleep metrics

    # Check that r values are between -1 and 1
    assert all(result['r'].between(-1, 1))

def test_benjamini_hochberg_correction():
    """Test BH correction with known values."""
    df = pd.DataFrame({
        'p': [0.01, 0.03, 0.04, 0.08]
    })

    result = apply_benjamini_hochberg(df)

    assert 'q' in result.columns
    assert len(result) == 4
    # Q-values should be >= corresponding p-values
    assert all(result['q'] >= result['p'])

def test_flag_correlations():
    """Test correlation flagging logic."""
    df = pd.DataFrame({
        'r': [0.1, 0.35, -0.4, 0.25],
        'q': [0.5, 0.03, 0.04, 0.06]
    })

    result = flag_correlations(df, r_threshold=0.3, q_threshold=0.05)

    assert 'is_moderate' in result.columns
    assert 'is_meaningful' in result.columns

    # Check flagging logic
    assert result.iloc[0]['is_moderate'] == False  # |0.1| <= 0.3
    assert result.iloc[1]['is_moderate'] == True   # |0.35| > 0.3
    assert result.iloc[2]['is_moderate'] == True   # |-0.4| > 0.3
    assert result.iloc[3]['is_moderate'] == False  # |0.25| <= 0.3

    assert result.iloc[0]['is_meaningful'] == False  # Not moderate
    assert result.iloc[1]['is_meaningful'] == True   # Moderate and q < 0.05
    assert result.iloc[2]['is_meaningful'] == True   # Moderate and q < 0.05
    assert result.iloc[3]['is_meaningful'] == False  # Not moderate

def test_empty_dataframe_handling():
    """Test handling of empty DataFrames."""
    empty_df = pd.DataFrame()

    result = calculate_spearman_correlation(empty_df, empty_df)
    assert result.empty

    result_bh = apply_benjamini_hochberg(empty_df)
    assert result_bh.empty

    result_flag = flag_correlations(empty_df)
    assert result_flag.empty

def test_handle_no_significant_associations():
    """Test the handling of no significant associations case."""
    # Case 1: Empty DataFrame
    empty_df = pd.DataFrame()
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_results.csv"
        result = handle_no_significant_associations(empty_df, output_path)

        assert result.empty
        assert 'status' in result.columns
        assert all(result['status'] == 'no_significant_associations')
        assert output_path.exists()

    # Case 2: DataFrame with no meaningful correlations
    df_no_sig = pd.DataFrame({
        'diversity_metric': ['shannon', 'simpson'],
        'sleep_metric': ['sleep_efficiency', 'sleep_duration_hours'],
        'r': [0.15, 0.20],
        'p': [0.4, 0.35],
        'q': [0.5, 0.45],
        'is_moderate': [False, False],
        'is_meaningful': [False, False]
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_results_no_sig.csv"
        result = handle_no_significant_associations(df_no_sig, output_path)

        assert len(result) == 2
        assert all(result['status'] == 'no_significant_associations')
        assert output_path.exists()

    # Case 3: DataFrame with some meaningful correlations
    df_with_sig = pd.DataFrame({
        'diversity_metric': ['shannon', 'simpson'],
        'sleep_metric': ['sleep_efficiency', 'sleep_duration_hours'],
        'r': [0.35, 0.15],
        'p': [0.03, 0.4],
        'q': [0.04, 0.5],
        'is_moderate': [True, False],
        'is_meaningful': [True, False]
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_results_with_sig.csv"
        result = handle_no_significant_associations(df_with_sig, output_path)

        assert len(result) == 2
        assert result.iloc[0]['status'] == 'significant'
        assert result.iloc[1]['status'] == 'non_significant'
        assert output_path.exists()