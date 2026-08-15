"""
Unit tests for T046: verify_gate.py logic.

Tests the gate verification logic by simulating missing, invalid, and valid files.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.scripts.verify_gate import (
    check_file_exists,
    check_file_valid_json,
    check_source_id_valid
)

class TestGateVerification:
    
    def test_check_file_exists_missing(self, tmp_path):
        """Test that check_file_exists returns False for missing file."""
        missing_file = tmp_path / "nonexistent.json"
        assert check_file_exists(missing_file) is False

    def test_check_file_exists_present(self, tmp_path):
        """Test that check_file_exists returns True for existing file."""
        existing_file = tmp_path / "exists.json"
        existing_file.write_text("{}")
        assert check_file_exists(existing_file) is True

    def test_check_file_valid_json_invalid(self, tmp_path, caplog):
        """Test that check_file_valid_json returns False for invalid JSON."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ this is not json }")
        
        # Suppress logging output for cleaner test runs if needed, 
        # but we want to ensure the function returns False.
        result = check_file_valid_json(invalid_file)
        assert result is False

    def test_check_file_valid_json_valid(self, tmp_path):
        """Test that check_file_valid_json returns True for valid JSON."""
        valid_file = tmp_path / "valid.json"
        valid_file.write_text('{"key": "value"}')
        assert check_file_valid_json(valid_file) is True

    def test_check_source_id_valid_missing_id(self, tmp_path, caplog):
        """Test that check_source_id_valid returns False if dataset_id is missing."""
        valid_json_no_id = tmp_path / "no_id.json"
        valid_json_no_id.write_text('{"source_name": "test"}')
        
        result = check_source_id_valid(valid_json_no_id)
        assert result is False

    def test_check_source_id_valid_empty_id(self, tmp_path, caplog):
        """Test that check_source_id_valid returns False if dataset_id is empty."""
        empty_id_json = tmp_path / "empty_id.json"
        empty_id_json.write_text('{"dataset_id": ""}')
        
        result = check_source_id_valid(empty_id_json)
        assert result is False

    def test_check_source_id_valid_missing_file(self, tmp_path, caplog):
        """Test that check_source_id_valid returns False if file is missing."""
        missing_file = tmp_path / "missing.json"
        
        result = check_source_id_valid(missing_file)
        assert result is False

    def test_check_source_id_valid_success(self, tmp_path):
        """Test that check_source_id_valid returns True for valid dataset_id."""
        valid_json = tmp_path / "valid.json"
        valid_json.write_text('{"dataset_id": "ds000001"}')
        
        result = check_source_id_valid(valid_json)
        assert result is True
