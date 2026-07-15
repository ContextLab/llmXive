"""
Integration tests for real data runner module.
"""
import os
import pytest
import pandas as pd
from code.analysis.real_data_runner import (
    run_ttest_on_dataset,
    run_anova_on_dataset,
    run_chi_squared_on_dataset,
    save_p_values_to_csv,
    load_p_values_to_csv_safe
)

@pytest.fixture
def sample_ttest_data():
    """Create sample data for t-test."""
    data = {
        'value': [1.0, 2.0, 3.0, 4.0, 5.0, 10.0, 11.0, 12.0, 13.0, 14.0],
        'group': ['A'] * 5 + ['B'] * 5
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_anova_data():
    """Create sample data for ANOVA."""
    data = {
        'value': [1.0, 2.0, 3.0, 10.0, 11.0, 12.0, 20.0, 21.0, 22.0],
        'group': ['A'] * 3 + ['B'] * 3 + ['C'] * 3
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_chi2_data():
    """Create sample data for chi-squared test."""
    data = {
        'row_cat': ['A', 'A', 'B', 'B', 'A', 'B', 'A', 'B'],
        'col_cat': ['X', 'Y', 'X', 'Y', 'X', 'Y', 'Y', 'X']
    }
    return pd.DataFrame(data)

def test_ttest_on_sample_data(sample_ttest_data):
    """Test t-test on sample data."""
    result = run_ttest_on_dataset(sample_ttest_data, 'value', 'group')
    assert 'statistic' in result
    assert 'p_value' in result
    assert not pd.isna(result['p_value'])

def test_anova_on_sample_data(sample_anova_data):
    """Test ANOVA on sample data."""
    result = run_anova_on_dataset(sample_anova_data, 'value', 'group')
    assert 'statistic' in result
    assert 'p_value' in result
    assert not pd.isna(result['p_value'])

def test_chi_squared_on_sample_data(sample_chi2_data):
    """Test chi-squared test on sample data."""
    result = run_chi_squared_on_dataset(sample_chi2_data, 'row_cat', 'col_cat')
    assert 'statistic' in result
    assert 'p_value' in result
    assert not pd.isna(result['p_value'])

def test_save_and_load_pvalues(tmp_path):
    """Test saving and loading p-values to/from CSV."""
    test_results = [
        {'test': 't-test', 'p_value': 0.05, 'statistic': 2.5},
        {'test': 'anova', 'p_value': 0.01, 'statistic': 5.0}
    ]
    
    output_file = tmp_path / "test_pvalues.csv"
    save_p_values_to_csv(test_results, str(output_file))
    
    assert os.path.exists(output_file)
    
    loaded_results = load_p_values_to_csv_safe(str(output_file))
    assert len(loaded_results) == len(test_results)
    assert loaded_results[0]['test'] == 't-test'
    assert abs(loaded_results[0]['p_value'] - 0.05) < 1e-6
