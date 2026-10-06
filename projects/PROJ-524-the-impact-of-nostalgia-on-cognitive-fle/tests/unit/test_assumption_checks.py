"""
Unit tests for Task T052: Statistical Assumption Checks.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from scipy import stats

# Import the module functions
from assumption_checks import (
    check_normality_shapiro,
    check_homogeneity_levene,
    run_assumption_checks,
    load_cleaned_dataset
)

@pytest.fixture
def sample_df():
    """Create a sample dataframe for testing."""
    np.random.seed(42)
    n = 100
    data = {
        'stimulus_type': np.random.choice(['nostalgia', 'control'], n),
        'perseverative_errors': np.random.normal(10, 2, n),
        'categories_completed': np.random.normal(5, 1, n)
    }
    return pd.DataFrame(data)

@pytest.fixture
def df_small_sample():
    """Create a dataframe with small sample size."""
    data = {
        'stimulus_type': ['nostalgia', 'nostalgia', 'control'],
        'perseverative_errors': [1.0, 2.0, 3.0],
        'categories_completed': [4.0, 5.0, 6.0]
    }
    return pd.DataFrame(data)

def test_check_normality_shapiro_passed(sample_df):
    """Test Shapiro-Wilk when normality holds (simulated data is normal)."""
    result = check_normality_shapiro(sample_df, 'perseverative_errors')
    
    assert 'nostalgia' in result
    assert 'control' in result
    assert result['nostalgia']['statistic'] is not None
    assert result['nostalgia']['p_value'] is not None
    # Note: With random normal data, p-value might be > 0.05 (passed)
    # We just assert the structure is correct.

def test_check_normality_shapiro_small_sample(df_small_sample):
    """Test Shapiro-Wilk with insufficient sample size."""
    result = check_normality_shapiro(df_small_sample, 'perseverative_errors')
    
    # One group might have only 1 or 2 samples
    for group, res in result.items():
        if res['status'] == 'skipped':
            assert 'Sample size < 3' in res['reason']

def test_check_homogeneity_levene(sample_df):
    """Test Levene's test for homogeneity."""
    result = check_homogeneity_levene(sample_df, 'perseverative_errors')
    
    assert result['statistic'] is not None
    assert result['p_value'] is not None
    assert result['status'] in ['passed', 'failed']

def test_check_homogeneity_levene_single_group(sample_df):
    """Test Levene's test with only one group."""
    single_group_df = sample_df[sample_df['stimulus_type'] == 'nostalgia']
    result = check_homogeneity_levene(single_group_df, 'perseverative_errors')
    
    assert result['status'] == 'skipped'
    assert 'Less than 2 groups' in result['reason']

@patch('assumption_checks.load_cleaned_dataset')
def test_run_assumption_checks(mock_load, sample_df):
    """Test the full run_assumption_checks function."""
    mock_load.return_value = sample_df
    
    report = run_assumption_checks()
    
    assert 'timestamp' in report
    assert 'checks' in report
    assert 'perseverative_errors' in report['checks']
    assert 'categories_completed' in report['checks']
    assert 'summary' in report
    assert 'assumptions_met' in report['summary']
