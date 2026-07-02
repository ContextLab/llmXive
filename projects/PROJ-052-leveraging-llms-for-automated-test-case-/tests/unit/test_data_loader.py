"""
Unit tests for data_loader.py
"""
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import os

# Import the module under test
from code.data_loader import (
    extract_bug_fix_description,
    extract_changed_lines,
    compute_sha256,
    verify_data_integrity,
    save_data_hash
)


class TestExtractBugFixDescription:
    """Tests for extract_bug_fix_description function."""

    def test_returns_description_from_known_column(self):
        """Test that the function returns the description from a known column."""
        data = {
            "project_name": "ExampleProject",
            "bug_id": "123",
            "description": "This is a test bug description."
        }
        row = pd.Series(data)
        result = extract_bug_fix_description(row)
        assert result == "This is a test bug description."

    def test_fallback_to_alternative_columns(self):
        """Test that the function tries alternative column names."""
        data = {
            "project_name": "ExampleProject",
            "bug_id": "123",
            "issue_description": "Alternative description found."
        }
        row = pd.Series(data)
        result = extract_bug_fix_description(row)
        assert result == "Alternative description found."

    def test_fallback_construction_when_no_description(self):
        """Test that the function constructs a fallback description."""
        data = {
            "project_name": "MyProject",
            "bug_id": "456"
        }
        row = pd.Series(data)
        result = extract_bug_fix_description(row)
        assert "MyProject" in result
        assert "456" in result

    def test_handles_missing_columns_gracefully(self):
        """Test that the function handles completely missing description fields."""
        data = {
            "other_field": "value"
        }
        row = pd.Series(data)
        result = extract_bug_fix_description(row)
        assert isinstance(result, str)
        assert len(result) > 0


class TestExtractChangedLines:
    """Tests for extract_changed_lines function."""

    def test_parses_comma_separated_string(self):
        """Test parsing of comma-separated line numbers."""
        data = {
            "changed_lines": "10, 20, 30"
        }
        row = pd.Series(data)
        result = extract_changed_lines(row)
        assert result == [10, 20, 30]

    def test_returns_list_directly(self):
        """Test handling of list input."""
        data = {
            "changed_lines": [5, 15, 25]
        }
        row = pd.Series(data)
        result = extract_changed_lines(row)
        assert result == [5, 15, 25]

    def test_returns_single_int_as_list(self):
        """Test handling of single integer input."""
        data = {
            "changed_lines": 42
        }
        row = pd.Series(data)
        result = extract_changed_lines(row)
        assert result == [42]

    def test_returns_empty_list_for_missing_column(self):
        """Test that missing column returns empty list."""
        data = {
            "other_field": "value"
        }
        row = pd.Series(data)
        result = extract_changed_lines(row)
        assert result == []

    def test_handles_invalid_string_gracefully(self):
        """Test that invalid string format returns empty list."""
        data = {
            "changed_lines": "not, a, number"
        }
        row = pd.Series(data)
        result = extract_changed_lines(row)
        assert result == []


class TestSHA256Hashing:
    """Tests for SHA-256 hashing functions."""

    def test_compute_sha256_returns_hex_string(self):
        """Test that compute_sha256 returns a valid hex string."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test content")
            tmp_path = Path(tmp.name)
        
        try:
            hash_value = compute_sha256(tmp_path)
            assert isinstance(hash_value, str)
            assert len(hash_value) == 64  # SHA-256 hex length
            assert all(c in '0123456789abcdef' for c in hash_value)
        finally:
            os.unlink(tmp_path)

    def test_save_and_verify_hash(self):
        """Test saving and verifying a hash."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test content")
            tmp_path = Path(tmp.name)
        
        try:
            # Save hash
            save_data_hash(tmp_path)
            hash_file = tmp_path.with_suffix(tmp_path.suffix + ".sha256")
            assert hash_file.exists()
            
            # Verify
            assert verify_data_integrity(tmp_path) is True
        finally:
            os.unlink(tmp_path)
            if hash_file.exists():
                os.unlink(hash_file)

    def test_verify_returns_false_on_modification(self):
        """Test that verification fails if file is modified after hashing."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"original content")
            tmp_path = Path(tmp.name)
        
        try:
            # Save hash of original
            save_data_hash(tmp_path)
            
            # Modify file
            with open(tmp_path, 'wb') as f:
                f.write(b"modified content")
            
            # Verify should fail
            assert verify_data_integrity(tmp_path) is False
        finally:
            os.unlink(tmp_path)
            hash_file = tmp_path.with_suffix(tmp_path.suffix + ".sha256")
            if hash_file.exists():
                os.unlink(hash_file)