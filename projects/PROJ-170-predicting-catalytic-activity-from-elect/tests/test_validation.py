"""
Unit tests for code/utils/validation.py
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

import sys
import os
# Ensure code/ is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code.utils.validation import (
    verify_data_checksum,
    validate_schema,
    validate_no_null_targets,
    generate_checksum_file
)


class TestVerifyDataChecksum:
    def test_verify_success_with_expected_hash(self, tmp_path):
        """Test successful verification when expected hash is provided."""
        file_path = tmp_path / "test_data.txt"
        file_path.write_text("Hello, World!")
        
        # Compute hash manually to simulate expected value
        import hashlib
        expected_hash = hashlib.sha256("Hello, World!".encode()).hexdigest()

        result = verify_data_checksum(file_path, expected_hash=expected_hash)
        assert result is True

    def test_verify_failure_with_expected_hash(self, tmp_path):
        """Test verification failure when hash mismatches."""
        file_path = tmp_path / "test_data.txt"
        file_path.write_text("Hello, World!")
        
        wrong_hash = "0" * 64
        result = verify_data_checksum(file_path, expected_hash=wrong_hash)
        assert result is False

    def test_verify_from_file(self, tmp_path):
        """Test verification using a hash file."""
        file_path = tmp_path / "test_data.txt"
        file_path.write_text("Data content")
        
        import hashlib
        expected_hash = hashlib.sha256("Data content".encode()).hexdigest()
        
        hash_file = tmp_path / "hash.json"
        hash_file.write_text(json.dumps({"hash": expected_hash}))
        
        result = verify_data_checksum(file_path, hash_file_path=hash_file)
        assert result is True

    def test_file_not_found(self, tmp_path):
        """Test behavior when source file is missing."""
        result = verify_data_checksum(tmp_path / "missing.txt", expected_hash="123")
        assert result is False

    def test_hash_file_not_found(self, tmp_path):
        """Test behavior when hash file is missing."""
        file_path = tmp_path / "data.txt"
        file_path.write_text("Data")
        result = verify_data_checksum(file_path, hash_file_path=tmp_path / "missing_hash.json")
        assert result is False

    def test_invalid_hash_file_format(self, tmp_path):
        """Test behavior when hash file is malformed JSON or missing key."""
        file_path = tmp_path / "data.txt"
        file_path.write_text("Data")
        
        hash_file = tmp_path / "bad_hash.json"
        hash_file.write_text("not json")
        
        result = verify_data_checksum(file_path, hash_file_path=hash_file)
        assert result is False
        
        hash_file.write_text(json.dumps({"wrong_key": "value"}))
        result = verify_data_checksum(file_path, hash_file_path=hash_file)
        assert result is False


class TestValidateSchema:
    def test_schema_valid(self):
        """Test valid schema passes."""
        df = pd.DataFrame({
            "col_a": [1, 2],
            "col_b": [3.0, 4.0]
        })
        is_valid, errors = validate_schema(
            df, 
            required_columns=["col_a", "col_b"]
        )
        assert is_valid is True
        assert len(errors) == 0

    def test_missing_required_columns(self):
        """Test failure when required columns are missing."""
        df = pd.DataFrame({"col_a": [1, 2]})
        is_valid, errors = validate_schema(
            df,
            required_columns=["col_a", "col_b"]
        )
        assert is_valid is False
        assert "col_b" in errors[0]

    def test_unexpected_columns_strict(self):
        """Test failure in strict mode with unexpected columns."""
        df = pd.DataFrame({
            "col_a": [1, 2],
            "col_b": [3, 4],
            "col_c": [5, 6]
        })
        is_valid, errors = validate_schema(
            df,
            required_columns=["col_a", "col_b"],
            strict=True
        )
        assert is_valid is False
        assert "col_c" in errors[0]

    def test_dtype_mismatch(self):
        """Test failure when dtype does not match expectation."""
        df = pd.DataFrame({
            "col_a": ["string", "data"],
            "col_b": [1, 2]
        })
        is_valid, errors = validate_schema(
            df,
            required_columns=["col_a", "col_b"],
            dtype_checks={"col_a": "int64"} # Expecting int, got object
        )
        assert is_valid is False
        assert "dtype mismatch" in errors[0]

    def test_dtype_match(self):
        """Test success when dtype matches."""
        df = pd.DataFrame({
            "col_a": pd.array([1, 2], dtype="int64"),
            "col_b": [3.0, 4.0]
        })
        is_valid, errors = validate_schema(
            df,
            required_columns=["col_a", "col_b"],
            dtype_checks={"col_a": "int64", "col_b": "float64"}
        )
        assert is_valid is True


class TestValidateNoNullTargets:
    def test_no_nulls(self):
        """Test clean target column."""
        df = pd.DataFrame({"target": [1.0, 2.0, 3.0]})
        is_valid, count = validate_no_null_targets(df, "target")
        assert is_valid is True
        assert count == 0

    def test_with_nulls(self):
        """Test target column with NaNs."""
        df = pd.DataFrame({"target": [1.0, np.nan, 3.0]})
        is_valid, count = validate_no_null_targets(df, "target")
        assert is_valid is False
        assert count == 1

    def test_column_missing(self):
        """Test when target column does not exist."""
        df = pd.DataFrame({"other": [1, 2, 3]})
        is_valid, count = validate_no_null_targets(df, "target")
        assert is_valid is False
        assert count == -1


class TestGenerateChecksumFile:
    def test_generate_and_verify(self, tmp_path):
        """Test generating a checksum file and verifying it works."""
        file_path = tmp_path / "source.txt"
        file_path.write_text("Content to hash")
        
        hash_file = tmp_path / "hash.json"
        
        generated_hash = generate_checksum_file(file_path, hash_file)
        
        assert hash_file.exists()
        assert len(generated_hash) == 64 # SHA256 hex length
        
        # Verify the generated hash matches the file
        with open(hash_file) as f:
            data = json.load(f)
        
        assert data['hash'] == generated_hash
        
        # Use verify function to ensure it matches
        result = verify_data_checksum(file_path, hash_file_path=hash_file)
        assert result is True