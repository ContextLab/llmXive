"""
Unit tests for src/utils/validators.py
"""
import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from src.utils.validators import (
    validate_schema,
    validate_raw_data,
    validate_processed_data,
    check_missing_values,
    validate_data_load
)

class TestSchemaValidation:
    def test_validate_schema_pass(self):
        data = {
            "yield_strength": [1.0, 2.0],
            "composition_c": [0.1, 0.2],
            "composition_mn": [1.0, 1.5]
        }
        df = pd.DataFrame(data)
        schema = {"yield_strength": "float", "composition_c": "float"}
        is_valid, errors = validate_schema(df, schema)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_schema_missing_column(self):
        data = {"yield_strength": [1.0]}
        df = pd.DataFrame(data)
        schema = {"yield_strength": "float", "missing_col": "float"}
        is_valid, errors = validate_schema(df, schema)
        assert is_valid is False
        assert any("Missing required columns" in e for e in errors)

    def test_validate_schema_wrong_type(self):
        data = {"yield_strength": ["a", "b"]}
        df = pd.DataFrame(data)
        schema = {"yield_strength": "float"}
        is_valid, errors = validate_schema(df, schema)
        assert is_valid is False
        assert any("expected float" in e for e in errors)

class TestRawDataValidation:
    def test_validate_raw_data_pass(self):
        data = {
            "yield_strength": [100.0, 200.0],
            "composition_c": [0.1, 0.2],
            "composition_mn": [1.0, 1.5],
            "composition_cr": [0.5, 0.6],
            "composition_ni": [0.2, 0.3],
            "heat_treatment_temp": [500.0, 600.0],
            "cooling_rate": [10.0, 20.0],
            "holding_time": [30.0, 40.0]
        }
        df = pd.DataFrame(data)
        is_valid, errors = validate_raw_data(df)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_raw_data_missing_yield(self):
        data = {
            "yield_strength": [100.0, np.nan],
            "composition_c": [0.1, 0.2],
            "composition_mn": [1.0, 1.5],
            "composition_cr": [0.5, 0.6],
            "composition_ni": [0.2, 0.3],
            "heat_treatment_temp": [500.0, 600.0],
            "cooling_rate": [10.0, 20.0],
            "holding_time": [30.0, 40.0]
        }
        df = pd.DataFrame(data)
        is_valid, errors = validate_raw_data(df)
        assert is_valid is False
        assert any("missing values in 'yield_strength'" in e for e in errors)

class TestProcessedDataValidation:
    def test_validate_processed_data_pass(self):
        data = {
            "yield_strength": [100.0, 200.0],
            "composition_c": [0.1, 0.2],
            "composition_mn": [1.0, 1.5],
            "composition_cr": [0.5, 0.6],
            "composition_ni": [0.2, 0.3],
            "heat_treatment_temp": [500.0, 600.0],
            "cooling_rate": [10.0, 20.0],
            "holding_time": [30.0, 40.0],
            "c_mn_ratio": [0.1, 0.13],
            "cr_ni_ratio": [2.5, 2.0],
            "cooling_rate_holding_time_interaction": [300.0, 800.0],
            "c_cooling_rate_interaction": [1.0, 4.0]
        }
        df = pd.DataFrame(data)
        is_valid, errors = validate_processed_data(df)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_processed_data_missing_target(self):
        data = {
            "yield_strength": [100.0, np.nan],
            "composition_c": [0.1, 0.2],
            "composition_mn": [1.0, 1.5],
            "composition_cr": [0.5, 0.6],
            "composition_ni": [0.2, 0.3],
            "heat_treatment_temp": [500.0, 600.0],
            "cooling_rate": [10.0, 20.0],
            "holding_time": [30.0, 40.0],
            "c_mn_ratio": [0.1, 0.13],
            "cr_ni_ratio": [2.5, 2.0],
            "cooling_rate_holding_time_interaction": [300.0, 800.0],
            "c_cooling_rate_interaction": [1.0, 4.0]
        }
        df = pd.DataFrame(data)
        is_valid, errors = validate_processed_data(df)
        assert is_valid is False
        assert any("missing values in 'yield_strength'" in e for e in errors)

class TestMissingValues:
    def test_check_missing_values(self):
        data = {
            "col1": [1.0, np.nan, 3.0],
            "col2": [1.0, 2.0, 3.0]
        }
        df = pd.DataFrame(data)
        missing = check_missing_values(df)
        assert "col1" in missing
        assert missing["col1"] == pytest.approx(33.333, rel=1e-1)
        assert "col2" in missing
        assert missing["col2"] == 0.0

class TestDataLoadValidation:
    def test_validate_data_load_valid_csv(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
            df.to_csv(tmp.name, index=False)
            is_valid, errors = validate_data_load(tmp.name)
            assert is_valid is True
            assert len(errors) == 0
            os.unlink(tmp.name)

    def test_validate_data_load_not_found(self):
        is_valid, errors = validate_data_load("/nonexistent/path/file.csv")
        assert is_valid is False
        assert any("not found" in e for e in errors)

    def test_validate_data_load_empty_csv(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(b"col1,col2\n") # Header only
            tmp.flush()
            is_valid, errors = validate_data_load(tmp.name)
            assert is_valid is False
            assert any("empty" in e for e in errors)
            os.unlink(tmp.name)