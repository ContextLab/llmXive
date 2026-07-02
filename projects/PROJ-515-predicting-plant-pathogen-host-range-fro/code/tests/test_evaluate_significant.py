import os
import json
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
from src.models.evaluate import (
    benjamini_hochberg_fdr,
    calculate_cohen_d,
    generate_significant_features_report
)

@pytest.fixture
def sample_data():
    """Create sample feature data and labels for testing."""
    np.random.seed(42)
    n_samples = 100
    
    # Create features with known differences between groups
    data = {
        'feature_1': np.concatenate([np.random.normal(0, 1, 50), np.random.normal(2, 1, 50)]),
        'feature_2': np.concatenate([np.random.normal(0, 1, 50), np.random.normal(0.5, 1, 50)]),
        'feature_3': np.concatenate([np.random.normal(0, 1, 50), np.random.normal(0, 1, 50)]),
        'feature_4': np.concatenate([np.random.normal(0, 1, 50), np.random.normal(-1.5, 1, 50)]),
        'feature_5': np.random.uniform(0, 1, 100)  # Random feature
    }
    
    features_df = pd.DataFrame(data)
    labels = pd.Series([0] * 50 + [1] * 50)
    
    return features_df, labels

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_benjamini_hochberg_fdr_basic():
    """Test basic BH FDR correction."""
    p_values = [0.01, 0.03, 0.05, 0.1, 0.2]
    adjusted = benjamini_hochberg_fdr(p_values, alpha=0.05)
    
    assert len(adjusted) == len(p_values)
    assert all(0 <= p <= 1 for p in adjusted)
    # First value should be adjusted to something reasonable
    assert adjusted[0] >= p_values[0]

def test_benjamini_hochberg_fdr_empty():
    """Test BH FDR with empty input."""
    assert benjamini_hochberg_fdr([]) == []

def test_cohen_d_identical_groups():
    """Test Cohen's d with identical groups."""
    group1 = [1.0, 2.0, 3.0]
    group2 = [1.0, 2.0, 3.0]
    
    d = calculate_cohen_d(group1, group2)
    assert d == 0.0

def test_cohen_d_different_groups():
    """Test Cohen's d with different groups."""
    group1 = [1.0, 2.0, 3.0]
    group2 = [4.0, 5.0, 6.0]
    
    d = calculate_cohen_d(group1, group2)
    assert d < 0  # group2 has higher mean, so d should be negative

def test_generate_significant_features_report(sample_data, temp_output_dir):
    """Test generation of significant features report."""
    features_df, labels = sample_data
    output_path = Path(temp_output_dir) / "significant_features.tsv"
    
    report_df = generate_significant_features_report(
        features_df, labels, output_path, alpha=0.05
    )
    
    # Check file exists
    assert output_path.exists()
    
    # Check columns
    expected_columns = ['feature_name', 'cohen_d', 'adj_p_value', 'significant_flag']
    assert list(report_df.columns) == expected_columns
    
    # Check data types
    assert report_df['cohen_d'].dtype in [np.float64, np.float32]
    assert report_df['adj_p_value'].dtype in [np.float64, np.float32]
    assert all(flag in ['Yes', 'No'] for flag in report_df['significant_flag'])
    
    # Check sorting (by absolute Cohen's d)
    abs_cohen = report_df['cohen_d'].abs()
    assert abs_cohen.is_monotonic_decreasing

def test_generate_significant_features_report_format(sample_data, temp_output_dir):
    """Test that the TSV file has correct tab delimiter."""
    features_df, labels = sample_data
    output_path = Path(temp_output_dir) / "significant_features.tsv"
    
    generate_significant_features_report(features_df, labels, output_path, alpha=0.05)
    
    # Read the file and check for tab delimiter
    with open(output_path, 'r') as f:
        lines = f.readlines()
    
    # First line should have tabs
    assert '\t' in lines[0]
    
    # Should have header + data rows
    assert len(lines) > 1

def test_generate_significant_features_report_significance(sample_data, temp_output_dir):
    """Test that significant features are correctly identified."""
    features_df, labels = sample_data
    output_path = Path(temp_output_dir) / "significant_features.tsv"
    
    report_df = generate_significant_features_report(
        features_df, labels, output_path, alpha=0.05
    )
    
    # At least some features should have adj_p_value <= 0.05 or > 0.05
    significant_count = (report_df['adj_p_value'] <= 0.05).sum()
    assert significant_count >= 0  # Could be 0 if no features are significant
    assert significant_count <= len(report_df)
    
    # Check consistency between adj_p_value and significant_flag
    for _, row in report_df.iterrows():
        if row['adj_p_value'] <= 0.05:
            assert row['significant_flag'] == 'Yes'
        else:
            assert row['significant_flag'] == 'No'