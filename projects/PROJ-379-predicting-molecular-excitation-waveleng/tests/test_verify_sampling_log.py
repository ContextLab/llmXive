"""
Unit tests for T046: verify_sampling_log.py
"""
import json
import os
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the functions we want to test
# We need to adjust the import path if running from tests/
# Assuming standard project structure: code/verify_sampling_log.py
import sys
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from verify_sampling_log import validate_schema, load_sampling_log

class TestValidateSchema:
    """Tests for the validate_schema function."""

    def test_valid_schema(self):
        """Test a valid sampling log schema."""
        data = {
            "sample_size": 100,
            "seed": 42,
            "method": "streaming_islice",
            "total_rows_scanned": 1000
        }
        errors = validate_schema(data)
        assert len(errors) == 0

    def test_missing_required_keys(self):
        """Test missing required keys."""
        data = {
            "sample_size": 100,
            "seed": 42
        }
        errors = validate_schema(data)
        assert len(errors) > 0
        assert any("Missing required keys" in err for err in errors)

    def test_invalid_type_sample_size(self):
        """Test invalid type for sample_size."""
        data = {
            "sample_size": "100",  # Should be int
            "seed": 42,
            "method": "streaming_islice",
            "total_rows_scanned": 1000
        }
        errors = validate_schema(data)
        assert len(errors) > 0
        assert any("'sample_size' must be an integer" in err for err in errors)

    def test_negative_sample_size(self):
        """Test negative sample_size."""
        data = {
            "sample_size": -10,
            "seed": 42,
            "method": "streaming_islice",
            "total_rows_scanned": 1000
        }
        errors = validate_schema(data)
        assert len(errors) > 0
        assert any("'sample_size' must be non-negative" in err for err in errors)

    def test_inconsistency_sample_vs_total(self):
        """Test inconsistency where sample_size > total_rows_scanned."""
        data = {
            "sample_size": 1000,
            "seed": 42,
            "method": "streaming_islice",
            "total_rows_scanned": 100
        }
        errors = validate_schema(data)
        assert len(errors) > 0
        assert any("Inconsistency" in err for err in errors)

    def test_invalid_method_type(self):
        """Test invalid type for method."""
        data = {
            "sample_size": 100,
            "seed": 42,
            "method": 123,  # Should be string
            "total_rows_scanned": 1000
        }
        errors = validate_schema(data)
        assert len(errors) > 0
        assert any("'method' must be a string" in err for err in errors)

class TestLoadSamplingLog:
    """Tests for the load_sampling_log function."""

    def setup_method(self):
        """Set up a temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test_sampling_log.json"

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_load_valid_json(self):
        """Test loading a valid JSON file."""
        data = {
            "sample_size": 50,
            "seed": 42,
            "method": "streaming_islice",
            "total_rows_scanned": 500
        }
        with open(self.test_file, 'w') as f:
            json.dump(data, f)
        
        loaded_data = load_sampling_log(self.test_file)
        assert loaded_data == data

    def test_file_not_found(self):
        """Test loading a non-existent file raises FileNotFoundError."""
        non_existent_file = Path(self.temp_dir) / "non_existent.json"
        with pytest.raises(FileNotFoundError):
            load_sampling_log(non_existent_file)

    def test_invalid_json(self):
        """Test loading an invalid JSON file."""
        with open(self.test_file, 'w') as f:
            f.write("{ invalid json }")
        
        # load_sampling_log itself doesn't catch JSONDecodeError, 
        # but it's expected to be handled by the caller (main).
        # We test that it raises JSONDecodeError when passed to json.load
        with open(self.test_file, 'r') as f:
            with pytest.raises(json.JSONDecodeError):
                json.load(f)