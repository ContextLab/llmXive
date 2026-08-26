"""
Unit tests for validate_network_metrics_schema.py (Task T020)
"""
import csv
import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from validate_network_metrics_schema import (
    validate_row,
    validate_trace_id_format,
    EXPECTED_COLUMNS,
    EXPECTED_TYPES
)


class TestTraceIdValidation:
    def test_valid_trace_id(self):
        """Test that valid SHA-256 trace IDs pass validation"""
        valid_id = "a" * 64  # Valid hex string of length 64
        assert validate_trace_id_format(valid_id) is True

        valid_id = "0123456789abcdef" * 4  # Another valid pattern
        assert validate_trace_id_format(valid_id) is True

    def test_invalid_trace_id_short(self):
        """Test that short trace IDs fail validation"""
        assert validate_trace_id_format("a" * 32) is False

    def test_invalid_trace_id_non_hex(self):
        """Test that non-hex trace IDs fail validation"""
        assert validate_trace_id_format("g" * 64) is False
        assert validate_trace_id_format("A" * 64) is False  # Uppercase not allowed in hex pattern

    def test_invalid_trace_id_wrong_length(self):
        """Test that wrong length trace IDs fail validation"""
        assert validate_trace_id_format("a" * 63) is False
        assert validate_trace_id_format("a" * 65) is False


class TestRowValidation:
    def test_valid_row(self):
        """Test that a valid row passes validation"""
        valid_row = {
            "participant_id": "P001",
            "age": "45",
            "global_efficiency": "0.85",
            "local_efficiency": "0.72",
            "clustering_coeff": "0.68",
            "modularity": "0.45",
            "trace_id": "a" * 64,
            "signal_quality_flag": "OK"
        }
        errors = validate_row(valid_row, 1)
        assert len(errors) == 0

    def test_missing_column(self):
        """Test that missing columns are detected"""
        incomplete_row = {
            "participant_id": "P001",
            "age": "45",
            "global_efficiency": "0.85",
            # Missing other columns
        }
        errors = validate_row(incomplete_row, 1)
        assert len(errors) > 0
        assert any("Missing required column" in error for error in errors)

    def test_invalid_age_type(self):
        """Test that non-integer age fails validation"""
        row = {
            "participant_id": "P001",
            "age": "not_a_number",
            "global_efficiency": "0.85",
            "local_efficiency": "0.72",
            "clustering_coeff": "0.68",
            "modularity": "0.45",
            "trace_id": "a" * 64,
            "signal_quality_flag": "OK"
        }
        errors = validate_row(row, 1)
        assert len(errors) > 0
        assert any("Type conversion failed" in error for error in errors)

    def test_invalid_trace_id_format(self):
        """Test that invalid trace_id format is detected"""
        row = {
            "participant_id": "P001",
            "age": "45",
            "global_efficiency": "0.85",
            "local_efficiency": "0.72",
            "clustering_coeff": "0.68",
            "modularity": "0.45",
            "trace_id": "invalid",
            "signal_quality_flag": "OK"
        }
        errors = validate_row(row, 1)
        assert len(errors) > 0
        assert any("Invalid trace_id format" in error for error in errors)

    def test_nan_values(self):
        """Test that NaN values in float columns are detected"""
        row = {
            "participant_id": "P001",
            "age": "45",
            "global_efficiency": "nan",
            "local_efficiency": "0.72",
            "clustering_coeff": "0.68",
            "modularity": "0.45",
            "trace_id": "a" * 64,
            "signal_quality_flag": "OK"
        }
        errors = validate_row(row, 1)
        assert len(errors) > 0
        assert any("Invalid float value" in error for error in errors)

    def test_inf_values(self):
        """Test that Inf values in float columns are detected"""
        row = {
            "participant_id": "P001",
            "age": "45",
            "global_efficiency": "inf",
            "local_efficiency": "0.72",
            "clustering_coeff": "0.68",
            "modularity": "0.45",
            "trace_id": "a" * 64,
            "signal_quality_flag": "OK"
        }
        errors = validate_row(row, 1)
        assert len(errors) > 0
        assert any("Invalid float value" in error for error in errors)


class TestExpectedSchema:
    def test_expected_columns_defined(self):
        """Test that all required columns are defined"""
        required = [
            "participant_id",
            "age",
            "global_efficiency",
            "local_efficiency",
            "clustering_coeff",
            "modularity",
            "trace_id",
            "signal_quality_flag"
        ]
        assert set(EXPECTED_COLUMNS) == set(required)

    def test_expected_types_defined(self):
        """Test that all expected types are defined"""
        assert len(EXPECTED_TYPES) == len(EXPECTED_COLUMNS)
        for col in EXPECTED_COLUMNS:
            assert col in EXPECTED_TYPES