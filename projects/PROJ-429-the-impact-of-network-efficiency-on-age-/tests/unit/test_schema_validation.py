"""
Unit tests for schema validation logic.
"""

import pytest
from pathlib import Path
import json
import csv
import tempfile
import os

# Import the validation logic
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from code.validate_network_metrics_schema import validate_row, SCHEMA, REQUIRED_FIELDS

class TestSchemaValidation:
    """Tests for the schema validation functions."""

    def test_valid_row(self):
        """Test that a valid row passes validation."""
        valid_row = {
            "participant_id": "P001",
            "age": 45,
            "sex": "M",
            "education_years": 16,
            "global_efficiency": 0.45,
            "characteristic_path_length": 2.22,
            "local_efficiency": 0.38,
            "clustering_coefficient": 0.52,
            "modularity": 0.41,
            "signal_quality_flag": "Good",
            "trace_id": "a" * 64  # Valid 64-char hex string
        }
        
        is_valid, errors = validate_row(valid_row, SCHEMA)
        assert is_valid is True
        assert len(errors) == 0

    def test_missing_required_field(self):
        """Test that missing required fields are detected."""
        incomplete_row = {
            "participant_id": "P001",
            "age": 45,
            # Missing other required fields
            "trace_id": "a" * 64
        }
        
        is_valid, errors = validate_row(incomplete_row, SCHEMA)
        assert is_valid is False
        assert len(errors) > 0
        assert any("Missing required field" in err for err in errors)

    def test_invalid_sex_value(self):
        """Test that invalid sex values are detected."""
        row = {
            "participant_id": "P001",
            "age": 45,
            "sex": "INVALID",
            "education_years": 16,
            "global_efficiency": 0.45,
            "characteristic_path_length": 2.22,
            "local_efficiency": 0.38,
            "clustering_coefficient": 0.52,
            "modularity": 0.41,
            "signal_quality_flag": "Good",
            "trace_id": "a" * 64
        }
        
        is_valid, errors = validate_row(row, SCHEMA)
        assert is_valid is False
        assert any("invalid value" in err for err in errors)

    def test_invalid_trace_id_length(self):
        """Test that trace_id with wrong length is detected."""
        row = {
            "participant_id": "P001",
            "age": 45,
            "sex": "M",
            "education_years": 16,
            "global_efficiency": 0.45,
            "characteristic_path_length": 2.22,
            "local_efficiency": 0.38,
            "clustering_coefficient": 0.52,
            "modularity": 0.41,
            "signal_quality_flag": "Good",
            "trace_id": "abc"  # Too short
        }
        
        is_valid, errors = validate_row(row, SCHEMA)
        assert is_valid is False
        assert any("64-character" in err for err in errors)

    def test_invalid_trace_id_non_hex(self):
        """Test that non-hex trace_id is detected."""
        row = {
            "participant_id": "P001",
            "age": 45,
            "sex": "M",
            "education_years": 16,
            "global_efficiency": 0.45,
            "characteristic_path_length": 2.22,
            "local_efficiency": 0.38,
            "clustering_coefficient": 0.52,
            "modularity": 0.41,
            "signal_quality_flag": "Good",
            "trace_id": "g" * 64  # 'g' is not hex
        }
        
        is_valid, errors = validate_row(row, SCHEMA)
        assert is_valid is False
        assert any("hex string" in err for err in errors)

    def test_invalid_signal_quality_flag(self):
        """Test that invalid signal_quality_flag values are detected."""
        row = {
            "participant_id": "P001",
            "age": 45,
            "sex": "M",
            "education_years": 16,
            "global_efficiency": 0.45,
            "characteristic_path_length": 2.22,
            "local_efficiency": 0.38,
            "clustering_coefficient": 0.52,
            "modularity": 0.41,
            "signal_quality_flag": "Invalid Flag",
            "trace_id": "a" * 64
        }
        
        is_valid, errors = validate_row(row, SCHEMA)
        assert is_valid is False
        assert any("invalid value" in err for err in errors)

    def test_invalid_age_type(self):
        """Test that non-integer age is detected."""
        row = {
            "participant_id": "P001",
            "age": "forty-five",
            "sex": "M",
            "education_years": 16,
            "global_efficiency": 0.45,
            "characteristic_path_length": 2.22,
            "local_efficiency": 0.38,
            "clustering_coefficient": 0.52,
            "modularity": 0.41,
            "signal_quality_flag": "Good",
            "trace_id": "a" * 64
        }
        
        is_valid, errors = validate_row(row, SCHEMA)
        assert is_valid is False
        assert any("must be an integer" in err for err in errors)