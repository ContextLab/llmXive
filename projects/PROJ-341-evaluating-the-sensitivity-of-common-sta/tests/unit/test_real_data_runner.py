import os
import sys
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.analysis.real_data_runner import (
    load_prepared_data,
    run_ttest_on_dataset,
    run_anova_on_dataset,
    run_chi_squared_on_dataset
)

@pytest.fixture
def mock_ttest_df():
    """Create a mock DataFrame for t-test."""
    data = {
        'group': ['A'] * 10 + ['B'] * 10,
        'value': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21]
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_anova_df():
    """Create a mock DataFrame for ANOVA."""
    data = {
        'group': ['A'] * 10 + ['B'] * 10 + ['C'] * 10,
        'value': list(range(10)) + list(range(10, 20)) + list(range(20, 30))
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_chi_df():
    """Create a mock DataFrame for Chi-squared."""
    data = {
        'cat1': ['X'] * 20 + ['Y'] * 20,
        'cat2': ['P'] * 10 + ['Q'] * 10 + ['P'] * 15 + ['Q'] * 5
    }
    return pd.DataFrame(data)

def test_run_ttest(mock_ttest_df):
    result = run_ttest_on_dataset(mock_ttest_df, 'group', 'value')
    assert result['p_value'] is not None
    assert result['statistic'] is not None
    assert result['method'] == 't-test'
    assert result['dataset'] is None # Not set in function, set in caller

def test_run_anova(mock_anova_df):
    result = run_anova_on_dataset(mock_anova_df, 'group', 'value')
    assert result['p_value'] is not None
    assert result['statistic'] is not None
    assert result['method'] == 'anova'

def test_run_chi_squared(mock_chi_df):
    result = run_chi_squared_on_dataset(mock_chi_df, 'cat1', 'cat2')
    assert result['p_value'] is not None
    assert result['statistic'] is not None
    assert result['method'] == 'chi-squared'

def test_insufficient_data_ttest():
    data = {'group': ['A'], 'value': [1]}
    df = pd.DataFrame(data)
    result = run_ttest_on_dataset(df, 'group', 'value')
    assert result['p_value'] is None
    assert 'error' in result

def test_insufficient_groups_anova():
    data = {'group': ['A'] * 5, 'value': [1, 2, 3, 4, 5]}
    df = pd.DataFrame(data)
    result = run_anova_on_dataset(df, 'group', 'value')
    assert result['p_value'] is None
    assert 'error' in result

def test_insufficient_categories_chi():
    data = {'cat1': ['A'] * 5, 'cat2': ['B'] * 5}
    df = pd.DataFrame(data)
    result = run_chi_squared_on_dataset(df, 'cat1', 'cat2')
    assert result['p_value'] is None
    assert 'error' in result
