"""
Unit tests for T034: Cleanup and Refactoring utilities.
Verifies that the refactored utility functions work correctly.
"""

import pytest
import os
import tempfile
from pathlib import Path
import json
import logging

# Import refactored utilities
from code.refactored_utils import (
    safe_divide,
    normalize_feature_vector,
    calculate_sha256,
    validate_json_schema,
    read_json_safe,
    write_json_safe
)
from code.refactored_io import (
    read_csv_rows,
    write_csv_rows,
    read_json_file,
    write_json_file
)
from code.refactored_logging import setup_logger, get_pipeline_logger

class TestSafeDivide:
    def test_normal_division(self):
        assert safe_divide(10, 2) == 5.0

    def test_zero_denominator(self):
        assert safe_divide(10, 0) == 0.0
        assert safe_divide(10, 0, default=-1.0) == -1.0

    def test_float_division(self):
        assert abs(safe_divide(10, 3) - 3.333333) < 0.0001

class TestNormalizeFeatureVector:
    def test_zscore_normalization(self):
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        normalized = normalize_feature_vector(data, method="zscore")
        # Mean should be approx 0, std approx 1
        import numpy as np
        assert abs(np.mean(normalized)) < 1e-6
        assert abs(np.std(normalized) - 1.0) < 1e-6

    def test_minmax_normalization(self):
        data = [10.0, 20.0, 30.0]
        normalized = normalize_feature_vector(data, method="minmax")
        assert normalized[0] == 0.0
        assert normalized[-1] == 1.0

    def test_empty_list(self):
        assert normalize_feature_vector([]) == []

class TestSha256:
    def test_hash_calculation(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data")
            tmp_path = Path(tmp.name)

        try:
            hash_val = calculate_sha256(tmp_path)
            assert len(hash_val) == 64  # SHA256 hex length
            assert isinstance(hash_val, str)
        finally:
            os.unlink(tmp_path)

class TestJsonSchemaValidation:
    def test_valid_schema(self):
        data = {"a": 1, "b": 2}
        assert validate_json_schema(data, ["a", "b"]) is True

    def test_missing_keys(self):
        data = {"a": 1}
        assert validate_json_schema(data, ["a", "b"]) is False

class TestIoUtils:
    def test_write_and_read_csv(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            rows = [{"col1": "val1", "col2": "val2"}, {"col1": "val3", "col2": "val4"}]
            assert write_csv_rows(tmp_path, rows) is True
            
            read_rows = list(read_csv_rows(tmp_path))
            assert len(read_rows) == 2
            assert read_rows[0]["col1"] == "val1"
        finally:
            os.unlink(tmp_path)

    def test_write_and_read_json(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            data = {"key": "value", "num": 123}
            assert write_json_file(tmp_path, data) is True
            
            read_data = read_json_file(tmp_path)
            assert read_data["key"] == "value"
            assert read_data["num"] == 123
        finally:
            os.unlink(tmp_path)

class TestLogging:
    def test_setup_logger(self):
        logger = setup_logger("test_logger", level=logging.DEBUG)
        assert logger.name == "test_logger"
        assert logger.level == logging.DEBUG

    def test_get_pipeline_logger(self):
        logger = get_pipeline_logger()
        assert logger is not None
        assert "pipeline" in logger.name.lower() or logger.name == "llmxive_pipeline"
