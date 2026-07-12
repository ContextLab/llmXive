"""
Unit tests for refactored utility functions.
Tests the cleanup and refactoring implemented in T039.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

from utils.refactor_utils import (
    standardize_dataframe_columns,
    validate_dataframe_schema,
    safe_column_access,
    drop_constant_columns,
    format_large_number,
    ensure_directory_exists,
    write_json_with_timestamp,
    calculate_memory_usage,
    log_dataframe_info
)


class TestStandardizeDataFrameColumns:
    def test_lowercase_conversion(self):
        df = pd.DataFrame({'A B': [1, 2], 'C_D': [3, 4]})
        result = standardize_dataframe_columns(df)
        assert list(result.columns) == ['a_b', 'c_d']
    
    def test_space_replacement(self):
        df = pd.DataFrame({'Column With Spaces': [1, 2]})
        result = standardize_dataframe_columns(df)
        assert 'column_with_spaces' in result.columns
    
    def test_preserves_data(self):
        df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
        result = standardize_dataframe_columns(df)
        assert result['a'].tolist() == [1, 2, 3]
        assert result['b'].tolist() == [4, 5, 6]


class TestValidateDataFrameSchema:
    def test_valid_schema(self):
        df = pd.DataFrame({'a': [1], 'b': [2], 'c': [3]})
        result = validate_dataframe_schema(df, ['a', 'b'])
        assert result['valid'] is True
        assert result['missing_columns'] == []
    
    def test_missing_required_columns(self):
        df = pd.DataFrame({'a': [1]})
        result = validate_dataframe_schema(df, ['a', 'b', 'c'])
        assert result['valid'] is False
        assert set(result['missing_columns']) == {'b', 'c'}
    
    def test_strict_mode_unexpected_columns(self):
        df = pd.DataFrame({'a': [1], 'b': [2], 'c': [3]})
        result = validate_dataframe_schema(df, ['a'], ['b'], strict=True)
        assert result['valid'] is False
        assert 'c' in result['unexpected_columns']
    
    def test_total_columns_count(self):
        df = pd.DataFrame({'a': [1], 'b': [2], 'c': [3]})
        result = validate_dataframe_schema(df, ['a'])
        assert result['total_columns'] == 3


class TestSafeColumnAccess:
    def test_existing_column(self):
        df = pd.DataFrame({'a': [1, 2, 3]})
        result = safe_column_access(df, 'a')
        assert result.tolist() == [1, 2, 3]
    
    def test_missing_column_with_default(self):
        df = pd.DataFrame({'a': [1, 2, 3]})
        result = safe_column_access(df, 'b', default=0)
        assert result.tolist() == [0, 0, 0]
    
    def test_missing_column_raises(self):
        df = pd.DataFrame({'a': [1, 2, 3]})
        with pytest.raises(KeyError):
            safe_column_access(df, 'b', raise_on_missing=True)


class TestDropConstantColumns:
    def test_drop_truly_constant(self):
        df = pd.DataFrame({
            'a': [1, 1, 1],
            'b': [1, 2, 3],
            'c': [5, 5, 5]
        })
        result = drop_constant_columns(df)
        assert 'a' not in result.columns
        assert 'c' not in result.columns
        assert 'b' in result.columns
    
    def test_threshold_parameter(self):
        df = pd.DataFrame({
            'a': [1, 1, 1, 1, 1],  # 1 unique out of 5 (20%)
            'b': [1, 2, 3, 4, 5],  # 5 unique out of 5 (100%)
        })
        result = drop_constant_columns(df, threshold=0.3)
        assert 'a' not in result.columns
        assert 'b' in result.columns
    
    def test_no_constant_columns(self):
        df = pd.DataFrame({
            'a': [1, 2, 3],
            'b': [4, 5, 6]
        })
        result = drop_constant_columns(df)
        assert list(result.columns) == ['a', 'b']


class TestFormatLargeNumber:
    def test_thousands(self):
        assert format_large_number(1500) == "1.50K"
    
    def test_millions(self):
        assert format_large_number(2500000) == "2.50M"
    
    def test_billions(self):
        assert format_large_number(3500000000) == "3.50B"
    
    def test_trillions(self):
        assert format_large_number(4500000000000) == "4.50T"
    
    def test_small_numbers(self):
        assert format_large_number(42) == "42.00"


class TestEnsureDirectoryExists:
    def test_creates_new_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "new" / "nested" / "dir"
            result = ensure_directory_exists(new_dir)
            assert result.exists()
            assert result.is_dir()
    
    def test_existing_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = ensure_directory_exists(tmpdir)
            assert result.exists()


class TestWriteJsonWithTimestamp:
    def test_creates_file_with_timestamp(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.json"
            data = {"key": "value", "number": 42}
            
            result = write_json_with_timestamp(data, output_path)
            
            assert result.exists()
            assert result.suffix == ".json"
            
            # Verify content
            with open(result, 'r') as f:
                loaded = json.load(f)
            assert loaded == data
    
    def test_timestamp_in_filename(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "data.json"
            data = {"test": True}
            
            result = write_json_with_timestamp(data, output_path)
            
            # Filename should contain underscore and timestamp
            assert '_' in result.stem


class TestCalculateMemoryUsage:
    def test_memory_calculation(self):
        df = pd.DataFrame({
            'a': [1, 2, 3, 4, 5],
            'b': ['x', 'y', 'z', 'w', 'v']
        })
        
        result = calculate_memory_usage(df)
        
        assert 'total_mb' in result
        assert 'per_column_mb' in result
        assert 'num_rows' in result
        assert 'num_columns' in result
        assert result['num_rows'] == 5
        assert result['num_columns'] == 2
        assert result['total_mb'] > 0