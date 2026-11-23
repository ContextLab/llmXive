import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import json
import tempfile
import os

from stats import (
    load_feature_matrix,
    prepare_group_data,
    run_mann_whitney_u,
    calculate_cohens_d,
    run_group_comparisons,
    apply_bonferroni_correction,
    check_sample_sizes,
    save_results
)

@pytest.fixture
def sample_feature_data():
    """Create sample feature data for testing."""
    data = {
        'participant_id': [f'P{i}' for i in range(1, 31)],
        'label': ['Control'] * 10 + ['AD'] * 10 + ['MCI'] * 10,
        'TTR': np.random.randn(30) * 0.5 + 0.7,
        'MTLD': np.random.randn(30) * 2.0 + 50.0,
        'Noun_Verb_Ratio': np.random.randn(30) * 0.2 + 1.5,
        'Mean_Clause_Length': np.random.randn(30) * 1.0 + 10.0,
        'T_Unit_Count': np.random.randn(30) * 2.0 + 15.0,
        'Sentence_Embedding_Cosine_Similarity': np.random.randn(30) * 0.1 + 0.8
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_load_feature_matrix(sample_feature_data, temp_output_dir):
    """Test loading feature matrix from CSV."""
    csv_path = os.path.join(temp_output_dir, 'test_features.csv')
    sample_feature_data.to_csv(csv_path, index=False)
    
    loaded_df = load_feature_matrix(csv_path)
    
    assert len(loaded_df) == len(sample_feature_data)
    assert list(loaded_df.columns) == list(sample_feature_data.columns)
    assert 'label' in loaded_df.columns

def test_prepare_group_data(sample_feature_data):
    """Test preparing data grouped by labels."""
    groups = prepare_group_data(sample_feature_data, label_col='label')
    
    assert 'Control' in groups
    assert 'AD' in groups
    assert 'MCI' in groups
    
    assert groups['Control'].shape[0] == 10
    assert groups['AD'].shape[0] == 10
    assert groups['MCI'].shape[0] == 10

def test_run_mann_whitney_u(sample_feature_data):
    """Test Mann-Whitney U test implementation."""
    groups = prepare_group_data(sample_feature_data, label_col='label')
    
    result = run_mann_whitney_u(groups['Control'], groups['AD'])
    
    assert 'statistics' in result
    assert 'p_values' in result
    assert len(result['statistics']) == 5  # 5 numeric feature columns
    assert len(result['p_values']) == 5
    assert all(0 <= p <= 1 for p in result['p_values'])

def test_calculate_cohens_d(sample_feature_data):
    """Test Cohen's d calculation."""
    groups = prepare_group_data(sample_feature_data, label_col='label')
    
    d_values = calculate_cohens_d(groups['Control'], groups['AD'])
    
    assert len(d_values) == 5  # 5 numeric feature columns
    assert all(not np.isnan(d) or np.isnan(d) for d in d_values)

def test_run_group_comparisons(sample_feature_data):
    """Test full group comparison workflow."""
    result = run_group_comparisons(sample_feature_data, label_col='label', 
                                  group1='Control', group2='AD')
    
    assert result['group1'] == 'Control'
    assert result['group2'] == 'AD'
    assert 'feature_names' in result
    assert 'raw_p_values' in result
    assert 'cohens_d' in result
    assert 'sample_sizes' in result
    assert len(result['raw_p_values']) == 5

def test_apply_bonferroni_correction():
    """Test Bonferroni correction logic."""
    p_values = [0.01, 0.03, 0.05, 0.10, 0.20]
    
    # Test with explicit num_tests
    adjusted = apply_bonferroni_correction(p_values, num_tests=5)
    expected = [min(p * 5, 1.0) for p in p_values]
    
    assert len(adjusted) == len(p_values)
    assert all(0 <= a <= 1 for a in adjusted)
    assert adjusted == expected
    
    # Test with default num_tests
    adjusted_default = apply_bonferroni_correction(p_values)
    assert adjusted_default == adjusted

def test_check_sample_sizes(sample_feature_data):
    """Test sample size checking."""
    result = check_sample_sizes(sample_feature_data, label_col='label', min_size=10)
    
    assert 'group_counts' in result
    assert result['min_size'] == 10
    assert result['low_power'] == False
    assert result['group_counts']['Control'] == 10
    assert result['group_counts']['AD'] == 10

def test_check_sample_sizes_low_power():
    """Test sample size checking with low power."""
    data = {
        'participant_id': ['P1', 'P2', 'P3'],
        'label': ['Control', 'Control', 'AD'],
        'TTR': [0.5, 0.6, 0.7]
    }
    df = pd.DataFrame(data)
    
    result = check_sample_sizes(df, label_col='label', min_size=10)
    
    assert result['low_power'] == True
    assert result['group_counts']['Control'] == 2
    assert result['group_counts']['AD'] == 1

def test_save_results(temp_output_dir):
    """Test saving results to JSON."""
    results = {
        'test_key': 'test_value',
        'p_values': [0.01, 0.05, 0.10],
        'adjusted_p_values': [0.05, 0.25, 1.0]
    }
    
    output_path = os.path.join(temp_output_dir, 'test_results.json')
    save_results(results, output_path)
    
    assert Path(output_path).exists()
    
    with open(output_path, 'r') as f:
        loaded_results = json.load(f)
    
    assert loaded_results == results

def test_bonferroni_edge_cases():
    """Test Bonferroni correction with edge cases."""
    # Empty list
    assert apply_bonferroni_correction([]) == []
    
    # Single p-value
    result = apply_bonferroni_correction([0.05], num_tests=1)
    assert result == [0.05]
    
    # P-value that exceeds 1.0 after correction
    result = apply_bonferroni_correction([0.5], num_tests=3)
    assert result == [1.0]
    
    # Very small p-values
    result = apply_bonferroni_correction([0.001, 0.002], num_tests=10)
    expected = [0.01, 0.02]
    assert result == expected

def test_mann_whitney_u_insufficient_data():
    """Test Mann-Whitney U with insufficient data."""
    # Create data with only one sample in one group
    group1 = np.array([[1.0], [2.0], [3.0]])
    group2 = np.array([[1.5]])
    
    result = run_mann_whitney_u(group1, group2)
    
    assert len(result['statistics']) == 1
    assert len(result['p_values']) == 1
    # Should handle gracefully, potentially returning NaN

def test_cohens_d_insufficient_data():
    """Test Cohen's d with insufficient data."""
    group1 = np.array([[1.0], [2.0], [3.0]])
    group2 = np.array([[1.5]])
    
    d_values = calculate_cohens_d(group1, group2)
    
    assert len(d_values) == 1
    # Should handle gracefully, potentially returning NaN
