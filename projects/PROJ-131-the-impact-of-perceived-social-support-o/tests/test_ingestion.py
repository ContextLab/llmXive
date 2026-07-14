"""
Tests for the ingestion module validation logic.
"""

import os
import tempfile
import pytest
import pandas as pd
from pathlib import Path

# Import the module under test
from code.data.ingestion import (
    validate_raw_data_file,
    validate_schema_presence,
    run_ingestion_checks,
    E_MISSING_001,
    E_INVALID_FORMAT,
    E_SCHEMA_MISMATCH
)


class TestValidateRawDataFile:
    def test_file_exists_and_valid_extension(self):
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            tmp.write(b"col1,col2\n1,2\n")
            tmp_path = Path(tmp.name)

        try:
            result = validate_raw_data_file(tmp_path, ['.csv'])
            assert result is True
        finally:
            os.unlink(tmp_path)

    def test_file_not_found(self):
        fake_path = Path("/tmp/nonexistent_file_12345.csv")
        result = validate_raw_data_file(fake_path, ['.csv'])
        assert result is False

    def test_invalid_extension(self):
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
            tmp.write(b"some text")
            tmp_path = Path(tmp.name)

        try:
            result = validate_raw_data_file(tmp_path, ['.csv'])
            assert result is False
        finally:
            os.unlink(tmp_path)

    def test_empty_file(self):
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            # Write nothing
            tmp_path = Path(tmp.name)

        try:
            result = validate_raw_data_file(tmp_path, ['.csv'])
            assert result is False
        finally:
            os.unlink(tmp_path)


class TestValidateSchemaPresence:
    def test_all_columns_present(self):
        df = pd.DataFrame({"a": [1], "b": [2], "c": [3]})
        result = validate_schema_presence(df, ["a", "b", "c"], "test_ds")
        assert result is True

    def test_missing_columns(self):
        df = pd.DataFrame({"a": [1], "b": [2]})
        result = validate_schema_presence(df, ["a", "b", "c"], "test_ds")
        assert result is False

    def test_invalid_object(self):
        result = validate_schema_presence("not a dataframe", ["a"], "test_ds")
        assert result is False


class TestRunIngestionChecks:
    def test_csv_success(self):
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False, mode='w') as tmp:
            tmp.write("id,age,support\n1,25,5\n2,30,4\n")
            tmp_path = Path(tmp.name)

        try:
            result = run_ingestion_checks(
                tmp_path,
                "test_csv",
                ["id", "age", "support"],
                ['.csv']
            )
            assert result is True
        finally:
            os.unlink(tmp_path)

    def test_dta_success(self):
        # Create a simple temp .dta file using pandas
        df = pd.DataFrame({"id": [1, 2], "val": [10, 20]})
        with tempfile.NamedTemporaryFile(suffix='.dta', delete=False) as tmp:
            df.to_stata(tmp.name, write_index=False)
            tmp_path = Path(tmp.name)

        try:
            result = run_ingestion_checks(
                tmp_path,
                "test_dta",
                ["id", "val"],
                ['.dta']
            )
            assert result is True
        finally:
            os.unlink(tmp_path)

    def test_missing_columns_fail(self):
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False, mode='w') as tmp:
            tmp.write("id,age\n1,25\n")
            tmp_path = Path(tmp.name)

        try:
            result = run_ingestion_checks(
                tmp_path,
                "test_fail",
                ["id", "age", "missing_col"],
                ['.csv']
            )
            assert result is False
        finally:
            os.unlink(tmp_path)

    def test_unsupported_extension_fail(self):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as tmp:
            tmp.write('{"id": 1}')
            tmp_path = Path(tmp.name)

        try:
            result = run_ingestion_checks(
                tmp_path,
                "test_json",
                ["id"],
                ['.csv']
            )
            assert result is False
        finally:
            os.unlink(tmp_path)