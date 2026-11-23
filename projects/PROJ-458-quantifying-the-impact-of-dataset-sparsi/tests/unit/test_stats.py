import pytest
import pandas as pd
import numpy as np
import os
import json
from pathlib import Path

from statistical_analysis import apply_tukey_posthoc, load_metrics, perform_lmm_analysis

@pytest.fixture
def sample_metrics_df():
    """Create a sample metrics DataFrame for testing."""
    np.random.seed(42)
    data = {
        'sparsity_level': ['10%', '20%', '30%', '40%', '50%'] * 10,
        'model': ['gpr'] * 50,
        'seed': [1, 2, 3, 4, 5] * 10,
        'rmse': np.random.normal(0.5, 0.1, 50),
        'mae': np.random.normal(0.4, 0.08, 50),
        'variance': np.random.normal(0.05, 0.01, 50),
        'calibration_slope': np.random.normal(0.95, 0.05, 50)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_metrics_file(sample_metrics_df, tmp_path):
    """Create a temporary metrics CSV file."""
    metrics_path = tmp_path / "metrics.csv"
    sample_metrics_df.to_csv(metrics_path, index=False)
    return str(metrics_path)

def test_tukey_posthoc_significant_differences(sample_metrics_df):
    """Test that Tukey post-hoc test correctly identifies significant differences."""
    # Create data with clear differences between groups
    df = sample_metrics_df.copy()
    df.loc[df['sparsity_level'] == '10%', 'rmse'] = 0.3  # Lower RMSE
    df.loc[df['sparsity_level'] == '50%', 'rmse'] = 0.7  # Higher RMSE
    
    tukey_df, significant_pairs = apply_tukey_posthoc(df, value_col='rmse', group_col='sparsity_level', threshold=0.05)
    
    # Check that we got results
    assert len(tukey_df) > 0, "Tukey results should not be empty"
    assert 'group1' in tukey_df.columns
    assert 'group2' in tukey_df.columns
    assert 'p-adj' in tukey_df.columns
    
    # Check that significant pairs are identified
    assert len(significant_pairs) > 0, "Should identify at least some significant pairs"
    assert isinstance(significant_pairs, dict)

def test_tukey_posthoc_threshold_handling(sample_metrics_df):
    """Test that Tukey post-hoc respects the significance threshold."""
    tukey_df, significant_pairs_05 = apply_tukey_posthoc(sample_metrics_df, threshold=0.05)
    tukey_df, significant_pairs_01 = apply_tukey_posthoc(sample_metrics_df, threshold=0.01)
    
    # Stricter threshold should result in fewer or equal significant pairs
    assert len(significant_pairs_01) <= len(significant_pairs_05), \
        "Stricter threshold (0.01) should have fewer or equal significant pairs than 0.05"

def test_tukey_posthoc_output_format(sample_metrics_df):
    """Test that Tukey post-hoc returns correct data structures."""
    tukey_df, significant_pairs = apply_tukey_posthoc(sample_metrics_df)
    
    # Check DataFrame structure
    assert isinstance(tukey_df, pd.DataFrame)
    assert 'group1' in tukey_df.columns
    assert 'group2' in tukey_df.columns
    assert 'p-adj' in tukey_df.columns
    
    # Check dictionary structure
    assert isinstance(significant_pairs, dict)
    for key, value in significant_pairs.items():
        assert isinstance(key, str)
        assert isinstance(value, bool)

def test_lmm_analysis_basic(sample_metrics_df):
    """Test that LMM analysis runs without errors."""
    result = perform_lmm_analysis(sample_metrics_df)
    
    # Check that we got a result
    assert result is not None
    assert hasattr(result, 'summary')
    
    # Check that coefficients are present
    assert hasattr(result, 'params')
    assert len(result.params) > 0

def test_load_metrics_file_not_found(tmp_path):
    """Test that load_metrics raises appropriate error for missing file."""
    non_existent_path = tmp_path / "non_existent.csv"
    with pytest.raises(FileNotFoundError):
        load_metrics(str(non_existent_path))

def test_load_metrics_valid_file(temp_metrics_file):
    """Test that load_metrics correctly loads a valid CSV file."""
    df = load_metrics(temp_metrics_file)
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 50  # From fixture
    assert 'sparsity_level' in df.columns
    assert 'rmse' in df.columns
    assert 'model' in df.columns

def test_tukey_pair_format(sample_metrics_df):
    """Test that significant pair keys are formatted correctly."""
    _, significant_pairs = apply_tukey_posthoc(sample_metrics_df)
    
    for key in significant_pairs.keys():
        # Check format: "level1 vs level2"
        assert ' vs ' in key, f"Key '{key}' should contain ' vs '"
        parts = key.split(' vs ')
        assert len(parts) == 2, f"Key '{key}' should have exactly two parts"
        assert parts[0] != parts[1], "Group names should be different"
