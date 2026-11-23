"""
Unit tests for missing total_sales handling in metrics calculation.

Verifies that:
1. Missing total_sales triggers a warning log
2. Rows with missing sales are excluded from sales-dependent checks
3. Rows with missing sales are still included in frequency analysis
4. Metrics are calculated correctly regardless of sales data presence
"""
import pytest
import logging
import pandas as pd
import numpy as np
from io import StringIO
from code.metrics import process_draws_for_metrics, calculate_birthday_ratio, calculate_consecutive_ratio
from code.data_utils import load_draws_csv
import os
import tempfile

@pytest.fixture
def sample_draws_with_missing_sales():
    """Create a sample DataFrame with some rows missing total_sales."""
    data = """draw_date,numbers,total_sales,jackpot_amount
    2023-01-01,"[5, 12, 23, 34, 41, 49]",15000000,5000000
    2023-01-04,"[3, 11, 19, 27, 35, 42]",15500000,5200000
    2023-01-08,"[7, 14, 21, 28, 35, 42]",,5100000
    2023-01-11,"[1, 2, 3, 4, 5, 6]",16000000,5300000
    2023-01-15,"[32, 33, 34, 35, 36, 37]",,5400000
    2023-01-18,"[10, 20, 30, 40, 45, 48]",17000000,5500000"""
    
    df = pd.read_csv(StringIO(data))
    # Convert numbers string to list
    df['numbers'] = df['numbers'].apply(lambda x: eval(x))
    return df

@pytest.fixture
def caplog_custom():
    """Fixture to capture log messages."""
    with pytest.fixture(logging) as caplog:
        yield caplog

def test_calculate_birthday_ratio_with_known_inputs():
    """Test birthday ratio calculation with known inputs."""
    # All birthdays (1-31)
    assert calculate_birthday_ratio([1, 2, 3, 4, 5, 6]) == 1.0
    # No birthdays (>31)
    assert calculate_birthday_ratio([32, 33, 34, 35, 36, 37]) == 0.0
    # Mixed
    assert calculate_birthday_ratio([5, 12, 23, 34, 41, 49]) == 0.5
    assert calculate_birthday_ratio([3, 11, 19, 27, 35, 42]) == 2/3

def test_calculate_consecutive_ratio_with_known_inputs():
    """Test consecutive ratio calculation with known inputs."""
    # All consecutive
    assert calculate_consecutive_ratio([1, 2, 3, 4, 5, 6]) == 1.0
    # No consecutive
    assert calculate_consecutive_ratio([1, 3, 5, 7, 9, 11]) == 0.0
    # Some consecutive
    assert calculate_consecutive_ratio([32, 33, 34, 35, 36, 37]) == 1.0
    assert calculate_consecutive_ratio([5, 12, 23, 34, 41, 49]) == 0.0

def test_missing_sales_triggers_warning(caplog, sample_draws_with_missing_sales):
    """Test that missing total_sales triggers a warning log."""
    with caplog.at_level(logging.WARNING):
        results = process_draws_for_metrics(sample_draws_with_missing_sales)
    
    # Check that warnings were logged for missing sales
    warning_messages = [record.message for record in caplog.records if record.levelno == logging.WARNING]
    assert any("Missing total_sales" in msg for msg in warning_messages)

def test_missing_sales_excluded_from_sales_checks(sample_draws_with_missing_sales):
    """Test that rows with missing sales are marked as not having sales data."""
    results = process_draws_for_metrics(sample_draws_with_missing_sales)
    
    # Find rows that should have missing sales (indices 2 and 4)
    missing_sales_rows = [r for r in results if not r['has_sales_data']]
    
    assert len(missing_sales_rows) == 2
    assert all(r['total_sales'] is None for r in missing_sales_rows)

def test_missing_sales_retained_for_frequency_analysis(sample_draws_with_missing_sales):
    """Test that rows with missing sales are still included in results."""
    results = process_draws_for_metrics(sample_draws_with_missing_sales)
    
    # All rows should be in results
    assert len(results) == len(sample_draws_with_missing_sales)
    
    # Verify metrics are calculated for rows with missing sales
    missing_sales_metrics = [r for r in results if not r['has_sales_data']]
    assert all('birthday_cluster_ratio' in r for r in missing_sales_metrics)
    assert all('consecutive_pattern_count' in r for r in missing_sales_metrics)
    assert all('is_majority_birthday' in r for r in missing_sales_metrics)

def test_metrics_calculated_regardless_of_sales_presence(sample_draws_with_missing_sales):
    """Test that metrics are calculated correctly regardless of sales data."""
    results = process_draws_for_metrics(sample_draws_with_missing_sales)
    
    # Check specific known values
    # Row 0: [5, 12, 23, 34, 41, 49] -> birthday_ratio=0.5, consecutive=0.0
    row_0 = results[0]
    assert row_0['birthday_cluster_ratio'] == 0.5
    assert row_0['consecutive_pattern_count'] == 0.0
    
    # Row 3: [1, 2, 3, 4, 5, 6] -> birthday_ratio=1.0, consecutive=1.0
    row_3 = results[3]
    assert row_3['birthday_cluster_ratio'] == 1.0
    assert row_3['consecutive_pattern_count'] == 1.0
    
    # Row 4 (missing sales): [32, 33, 34, 35, 36, 37] -> birthday_ratio=0.0, consecutive=1.0
    row_4 = results[4]
    assert row_4['birthday_cluster_ratio'] == 0.0
    assert row_4['consecutive_pattern_count'] == 1.0
    assert not row_4['has_sales_data']

def test_process_draws_handles_nan_sales(sample_draws_with_missing_sales):
    """Test that NaN sales values are handled correctly."""
    # Introduce NaN in sales column
    sample_draws_with_missing_sales.loc[2, 'total_sales'] = np.nan
    
    results = process_draws_for_metrics(sample_draws_with_missing_sales)
    
    # Row 2 should be marked as missing sales data
    row_2 = results[2]
    assert not row_2['has_sales_data']
    assert row_2['total_sales'] is None
    # But metrics should still be calculated
    assert row_2['birthday_cluster_ratio'] is not None
    assert row_2['consecutive_pattern_count'] is not None

def test_empty_dataframe():
    """Test handling of empty DataFrame."""
    df = pd.DataFrame(columns=['draw_date', 'numbers', 'total_sales', 'jackpot_amount'])
    results = process_draws_for_metrics(df)
    assert len(results) == 0

def test_missing_numbers_row(sample_draws_with_missing_sales):
    """Test handling of rows with missing numbers."""
    sample_draws_with_missing_sales.loc[2, 'numbers'] = None
    
    results = process_draws_for_metrics(sample_draws_with_missing_sales)
    
    # Row with None numbers should be skipped
    assert len(results) == len(sample_draws_with_missing_sales) - 1
    assert 2 not in [r['draw_index'] for r in results]