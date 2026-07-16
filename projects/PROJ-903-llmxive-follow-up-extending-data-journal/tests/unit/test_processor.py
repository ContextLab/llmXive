"""
tests/unit/test_processor.py
Unit tests for code/data/processor.py
"""

import os
import json
import tempfile
from pathlib import Path

import pytest
import pandas as pd
import numpy as np

from code.data.processor import (
    detect_missing_values,
    handle_missing_values,
    MissingValueError,
    process_dataset
)


class TestDetectMissingValues:
    def test_no_missing_values(self):
        df = pd.DataFrame({'A': [1, 2, 3], 'B': ['x', 'y', 'z']})
        report = detect_missing_values(df)
        assert report['total_missing'] == 0
        assert report['is_empty'] is False
        assert len(report['columns_with_missing']) == 0

    def test_missing_values_present(self):
        df = pd.DataFrame({'A': [1, np.nan, 3], 'B': ['x', 'y', np.nan]})
        report = detect_missing_values(df)
        assert report['total_missing'] == 2
        assert report['missing_by_column']['A'] == 1
        assert report['missing_by_column']['B'] == 1
        assert 'A' in report['columns_with_missing']
        assert 'B' in report['columns_with_missing']

    def test_empty_dataframe(self):
        df = pd.DataFrame()
        report = detect_missing_values(df)
        assert report['total_missing'] == 0
        assert report['is_empty'] is True


class TestHandleMissingValues:
    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame({
            'num': [1.0, 2.0, np.nan, 4.0],
            'cat': ['a', 'b', np.nan, 'd'],
            'clean': [1, 2, 3, 4]
        })

    def test_drop_strategy(self, sample_df):
        cleaned_df, report = handle_missing_values(sample_df, strategy='drop')
        assert len(cleaned_df) == 2 # Rows 0 and 3 remain
        assert report['rows_dropped'] == 2
        assert cleaned_df['num'].isna().sum() == 0

    def test_impute_mean_strategy(self, sample_df):
        cleaned_df, report = handle_missing_values(sample_df, strategy='impute', numeric_strategy='mean')
        # Mean of [1, 2, 4] is 2.333
        assert cleaned_df.loc[2, 'num'] == pytest.approx(2.333, rel=0.01)
        assert report['imputed_values'] > 0
        assert cleaned_df['num'].isna().sum() == 0

    def test_impute_mode_strategy(self, sample_df):
        cleaned_df, report = handle_missing_values(sample_df, strategy='impute', categorical_strategy='mode')
        # Mode of ['a', 'b', 'd'] is 'a' (or any if tie, but 'a' is first here)
        assert cleaned_df.loc[2, 'cat'] in ['a', 'b', 'd']
        assert cleaned_df['cat'].isna().sum() == 0

    def test_drop_below_min_rows(self, sample_df):
        # If we drop rows, we might go below min_rows if threshold is strict
        # Here we have 4 rows, dropping 2 leaves 2. If min_rows=3, it should fail.
        with pytest.raises(MissingValueError, match="below the minimum required"):
            handle_missing_values(sample_df, strategy='drop', min_rows=3)

    def test_invalid_strategy(self, sample_df):
        with pytest.raises(MissingValueError, match="Unknown strategy"):
            handle_missing_values(sample_df, strategy='invalid')

    def test_empty_input_raises(self):
        with pytest.raises(MissingValueError, match="Cannot process an empty DataFrame"):
            handle_missing_values(pd.DataFrame())


class TestProcessDataset:
    def test_full_pipeline(self):
        # Create a temporary CSV with missing values
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("A,B,C\n1,2,3\n4,,6\n7,8,\n9,10,11\n")
            input_path = f.name

        output_path = input_path.replace('.csv', '_clean.csv')
        report_path = input_path.replace('.csv', '_report.json')

        try:
            report = process_dataset(
                input_path=input_path,
                output_path=output_path,
                report_path=report_path,
                strategy='drop'
            )

            # Verify output file exists
            assert os.path.exists(output_path)
            assert os.path.exists(report_path)

            # Verify report content
            assert 'detection' in report
            assert 'cleaning' in report
            assert report['detection']['total_missing'] == 2
            assert report['cleaning']['rows_dropped'] == 2 # Rows 1 and 2 dropped

            # Verify cleaned file content
            df = pd.read_csv(output_path)
            assert len(df) == 2 # Rows 0 and 3
            assert df['A'].isna().sum() == 0
        finally:
            # Cleanup
            if os.path.exists(input_path): os.remove(input_path)
            if os.path.exists(output_path): os.remove(output_path)
            if os.path.exists(report_path): os.remove(report_path)

    def test_missing_input_file(self):
        with pytest.raises(FileNotFoundError):
            process_dataset(
                input_path="non_existent_file.csv",
                output_path="out.csv"
            )