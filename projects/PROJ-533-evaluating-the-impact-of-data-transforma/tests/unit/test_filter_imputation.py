import pytest
import pandas as pd
import numpy as np
import csv
from pathlib import Path
import tempfile
import shutil

from code.filter_datasets import (
    calculate_missing_ratio,
    impute_missing_values,
    filter_by_missing_data,
    get_imputation_log_headers,
    get_exclusions_headers
)

class TestMissingRatio:
    def test_zero_missing(self):
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        assert calculate_missing_ratio(df, 'a') == 0.0

    def test_some_missing(self):
        df = pd.DataFrame({'a': [1, np.nan, 3, np.nan]})
        # 2 missing out of 4
        assert abs(calculate_missing_ratio(df, 'a') - 0.5) < 1e-6

    def test_all_missing(self):
        df = pd.DataFrame({'a': [np.nan, np.nan, np.nan]})
        assert calculate_missing_ratio(df, 'a') == 1.0

    def test_column_not_found(self):
        df = pd.DataFrame({'a': [1, 2, 3]})
        assert calculate_missing_ratio(df, 'b') == 0.0

class TestImputation:
    def test_impute_mean(self):
        df = pd.DataFrame({'a': [1.0, 2.0, np.nan, 4.0]})
        new_df, rate = impute_missing_values(df, 'a', 'mean')
        # Mean of 1, 2, 4 is 7/3 = 2.333...
        expected_val = 7/3
        assert abs(new_df.loc[2, 'a'] - expected_val) < 1e-6
        assert rate == 0.25

    def test_impute_median(self):
        df = pd.DataFrame({'a': [1.0, 2.0, np.nan, 4.0, 5.0]})
        new_df, rate = impute_missing_values(df, 'a', 'median')
        # Median of 1, 2, 4, 5 is (2+4)/2 = 3
        assert new_df.loc[2, 'a'] == 3.0
        assert rate == 0.2

class TestFilterByMissing:
    def test_passes_threshold(self):
        # 10% missing is exactly threshold, should pass if threshold is > 0.10
        # Task says > 10% exclude. So 0.10 should pass.
        df = pd.DataFrame({'a': [1.0] * 9 + [np.nan]}) # 1/10 = 0.1
        result_df, exclusions, logs = filter_by_missing_data(df, 'test_id', threshold=0.10)
        assert result_df is not None
        assert len(exclusions) == 0
        assert len(logs) == 1 # Logged because rate > 0

    def test_exceeds_threshold(self):
        # 11% missing, should exclude
        df = pd.DataFrame({'a': [1.0] * 89 + [np.nan] * 11}) # 11/100 = 0.11
        result_df, exclusions, logs = filter_by_missing_data(df, 'test_id', threshold=0.10)
        assert result_df is None
        assert len(exclusions) == 1
        assert exclusions[0]['dataset_id'] == 'test_id'
        assert exclusions[0]['reason'] == 'missing_rate'
        assert 'missing_rate: 11.0%' in exclusions[0]['details']

    def test_multiple_columns_exceed(self):
        df = pd.DataFrame({
            'a': [1.0] * 89 + [np.nan] * 11,
            'b': [1.0] * 89 + [np.nan] * 11
        })
        # Should fail on 'a' first
        result_df, exclusions, logs = filter_by_missing_data(df, 'test_id', threshold=0.10)
        assert result_df is None
        assert len(exclusions) == 1 # Exits immediately on first failure

class TestCSVHeaders:
    def test_imputation_log_headers(self):
        headers = get_imputation_log_headers()
        assert headers == ['dataset_id', 'variable', 'imputation_method', 'rate']

    def test_exclusions_headers(self):
        headers = get_exclusions_headers()
        assert headers == ['dataset_id', 'reason', 'details']