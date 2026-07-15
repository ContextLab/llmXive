import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

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
    def test_basic_standardization(self):
        df = pd.DataFrame({
            "Column One": [1, 2],
            "Column-Two": [3, 4],
            "Column Three": [5, 6]
        })
        result = standardize_dataframe_columns(df)
        expected_cols = ["column_one", "column_two", "column_three"]
        assert list(result.columns) == expected_cols

    def test_empty_dataframe(self):
        df = pd.DataFrame()
        result = standardize_dataframe_columns(df)
        assert result.empty

    def test_none_dataframe(self):
        result = standardize_dataframe_columns(None)
        assert isinstance(result, pd.DataFrame) and result.empty

    def test_special_characters_removal(self):
        df = pd.DataFrame({
            "Column@1": [1],
            "Column#2": [2],
            "Column$3": [3]
        })
        result = standardize_dataframe_columns(df)
        assert "$" not in str(result.columns[0])
        assert "#" not in str(result.columns[1])


class TestValidateDataFrameSchema:
    def test_valid_schema(self):
        df = pd.DataFrame({
            "col1": [1, 2],
            "col2": [3, 4],
            "col3": [5, 6]
        })
        result = validate_dataframe_schema(df, ["col1", "col2"])
        assert result["valid"] is True
        assert result["missing_required"] == []

    def test_missing_required_columns(self):
        df = pd.DataFrame({
            "col1": [1, 2]
        })
        result = validate_dataframe_schema(df, ["col1", "col2"])
        assert result["valid"] is False
        assert "col2" in result["missing_required"]

    def test_empty_dataframe(self):
        df = pd.DataFrame()
        result = validate_dataframe_schema(df, ["col1"])
        assert result["valid"] is False
        assert "col1" in result["missing_required"]

    def test_column_types_recorded(self):
        df = pd.DataFrame({
            "int_col": [1, 2],
            "float_col": [1.5, 2.5],
            "str_col": ["a", "b"]
        })
        result = validate_dataframe_schema(df, ["int_col", "float_col", "str_col"])
        assert "int_col" in result["column_types"]
        assert "float_col" in result["column_types"]
        assert "str_col" in result["column_types"]


class TestSafeColumnAccess:
    def test_existing_column(self):
        df = pd.DataFrame({"col1": [1, 2, 3]})
        result = safe_column_access(df, "col1")
        assert list(result) == [1, 2, 3]

    def test_missing_column_with_default(self):
        df = pd.DataFrame({"col1": [1, 2, 3]})
        result = safe_column_access(df, "missing_col", default=999)
        assert list(result) == [999, 999, 999]

    def test_none_dataframe(self):
        result = safe_column_access(None, "col1", default=42)
        assert list(result) == [42]


class TestDropConstantColumns:
    def test_remove_constant_columns(self):
        df = pd.DataFrame({
            "constant": [5, 5, 5],
            "variable": [1, 2, 3],
            "another_constant": [0, 0, 0]
        })
        result = drop_constant_columns(df)
        assert "constant" not in result.columns
        assert "another_constant" not in result.columns
        assert "variable" in result.columns

    def test_no_constant_columns(self):
        df = pd.DataFrame({
            "col1": [1, 2, 3],
            "col2": [4, 5, 6]
        })
        result = drop_constant_columns(df)
        assert len(result.columns) == 2

    def test_empty_dataframe(self):
        df = pd.DataFrame()
        result = drop_constant_columns(df)
        assert result.empty


class TestFormatLargeNumber:
    def test_small_number(self):
        assert format_large_number(999) == "999.00"

    def test_thousands(self):
        result = format_large_number(1500)
        assert "K" in result

    def test_millions(self):
        result = format_large_number(2500000)
        assert "M" in result

    def test_billions(self):
        result = format_large_number(3500000000)
        assert "B" in result

    def test_precision(self):
        result = format_large_number(1234.5678, precision=1)
        assert "1.2K" in result


class TestEnsureDirectoryExists:
    def test_create_new_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "new_subdir"
            result = ensure_directory_exists(new_dir)
            assert result.exists()
            assert result.is_dir()

    def test_existing_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = ensure_directory_exists(tmpdir)
            assert result.exists()


class TestWriteJsonWithTimestamp:
    def test_write_json_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data = {"key": "value", "number": 42}
            file_path = write_json_with_timestamp(data, tmpdir, "test")
            
            assert file_path.exists()
            assert file_path.suffix == ".json"
            
            with open(file_path, 'r') as f:
                loaded = json.load(f)
            assert loaded == data

    def test_timestamp_in_filename(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = write_json_with_timestamp({}, tmpdir, "prefix")
            filename = file_path.name
            # Should contain timestamp format YYYYMMDD_HHMMSS
            assert "_" in filename and len(filename) > 20


class TestCalculateMemoryUsage:
    def test_memory_calculation(self):
        df = pd.DataFrame({
            "int_col": [1, 2, 3, 4, 5],
            "float_col": [1.1, 2.2, 3.3, 4.4, 5.5]
        })
        result = calculate_memory_usage(df)
        
        assert result["total_memory_bytes"] > 0
        assert result["total_memory_mb"] > 0
        assert "int_col" in result["per_column_memory"]
        assert "float_col" in result["per_column_memory"]

    def test_empty_dataframe(self):
        df = pd.DataFrame()
        result = calculate_memory_usage(df)
        assert result["total_memory_bytes"] == 0
        assert result["total_memory_mb"] == 0.0


class TestLogDataFrameInfo:
    def test_log_info(self):
        df = pd.DataFrame({
            "col1": [1, 2, 3],
            "col2": ["a", "b", "c"]
        })
        # Just ensure it doesn't raise an exception
        log_dataframe_info(df, "test_logger")

    def test_none_dataframe(self):
        # Should not raise exception
        log_dataframe_info(None, "test_logger")

    def test_empty_dataframe(self):
        df = pd.DataFrame()
        # Should not raise exception
        log_dataframe_info(df, "test_logger")