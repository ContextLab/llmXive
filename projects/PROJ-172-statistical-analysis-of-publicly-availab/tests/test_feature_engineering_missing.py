import pandas as pd
import numpy as np
import pytest
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from feature_engineering import handle_missing_advanced_metrics, calculate_advanced_metrics

@pytest.fixture
def sample_df_with_missing():
    """Create a sample DataFrame with missing advanced metrics."""
    data = {
        'team': ['NYY', 'BOS', 'NYY', 'BOS', 'NYY', 'BOS'],
        'year': [2019, 2019, 2020, 2020, 2021, 2021],
        'hits': [10, 8, 12, 0, 9, 11],
        'at_bats': [35, 32, 38, 30, 34, 36],
        'earned_runs': [4, 3, 5, 2, 3, 4],
        'innings_pitched': [9.0, 9.0, 9.0, 8.0, 9.0, 9.0],
        'bb': [3, 2, 4, 1, 2, 3],
        'hbp': [0, 1, 0, 0, 1, 0],
        'singles': [5, 4, 6, 0, 4, 5],
        'doubles': [2, 1, 2, 0, 2, 2],
        'triples': [0, 0, 0, 0, 0, 0],
        'hr': [3, 3, 4, 0, 3, 4],
        'ab': [35, 32, 38, 30, 34, 36],
        'k': [8, 7, 9, 5, 7, 8],
        'sf': [0, 0, 0, 0, 0, 0],
        'ibb': [0, 0, 0, 0, 0, 0],
        'run_expectancy': [0.5, 0.4, 0.6, 0.3, 0.5, 0.5]
    }
    df = pd.DataFrame(data)
    
    # Introduce missing values in wOBA (simulated by not calculating it first)
    # We will calculate advanced metrics first, then introduce NaNs
    df = calculate_advanced_metrics(df)
    
    # Manually set some wOBA and BABIP to NaN to test imputation
    df.loc[df['year'] == 2020, 'wOBA'] = np.nan
    df.loc[df['year'] == 2021, 'BABIP'] = np.nan
    
    return df

def test_handle_missing_advanced_metrics_imputation(sample_df_with_missing):
    """Test that missing values are imputed with league averages."""
    df, stats = handle_missing_advanced_metrics(sample_df_with_missing, 'year')
    
    # Check that no NaNs remain in advanced columns
    advanced_cols = ['wOBA', 'BABIP', 'park_adj_RE']
    for col in advanced_cols:
        if col in df.columns:
            assert not df[col].isna().any(), f"Column {col} still contains NaN values after imputation."
    
    # Check that imputation stats are recorded
    assert stats['imputed_rows'] > 0, "Expected some rows to be imputed."
    assert stats['total_rows'] == len(sample_df_with_missing)
    
def test_handle_missing_advanced_metrics_systemic_exclusion():
    """Test that rows with systemic missingness (>50% of year) are excluded."""
    data = {
        'team': ['A', 'A', 'A', 'B', 'B', 'B'],
        'year': [2020, 2020, 2020, 2021, 2021, 2021],
        'wOBA': [0.3, np.nan, np.nan, 0.3, 0.3, 0.3], # 2 out of 3 missing in 2020 (>50%)
        'BABIP': [0.3, 0.3, 0.3, 0.3, 0.3, 0.3],
        'park_adj_RE': [0.3, 0.3, 0.3, 0.3, 0.3, 0.3]
    }
    df = pd.DataFrame(data)
    
    df_result, stats = handle_missing_advanced_metrics(df, 'year')
    
    # The two rows from 2020 with missing wOBA should be excluded
    # because >50% of 2020 data is missing for wOBA
    assert len(df_result) < len(df), "Expected rows to be excluded due to systemic missingness."
    assert stats['excluded_rows'] > 0, "Expected some rows to be excluded."
    
def test_handle_missing_advanced_metrics_no_missing():
    """Test behavior when no missing values exist."""
    data = {
        'team': ['A', 'B'],
        'year': [2020, 2020],
        'wOBA': [0.3, 0.35],
        'BABIP': [0.3, 0.32],
        'park_adj_RE': [0.5, 0.5]
    }
    df = pd.DataFrame(data)
    
    df_result, stats = handle_missing_advanced_metrics(df, 'year')
    
    assert len(df_result) == len(df), "No rows should be excluded or imputed."
    assert stats['imputed_rows'] == 0, "No imputation should occur."
    assert stats['excluded_rows'] == 0, "No exclusion should occur."