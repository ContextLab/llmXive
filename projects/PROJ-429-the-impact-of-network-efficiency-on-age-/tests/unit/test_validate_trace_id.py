"""
Unit tests for T019: validate_trace_id.py
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from validate_trace_id import validate_trace_id_format, main

class TestValidateTraceIdFormat:
    """Tests for the validate_trace_id_format helper function."""
    
    def test_valid_sha256_lowercase(self):
        """Valid lowercase SHA-256 string."""
        valid_hash = "a" * 64
        assert validate_trace_id_format(valid_hash) is True
    
    def test_valid_sha256_uppercase(self):
        """Valid uppercase SHA-256 string (should fail as we expect lowercase hex)."""
        # Our regex uses [a-f0-9], so uppercase should fail
        invalid_hash = "A" * 64
        assert validate_trace_id_format(invalid_hash) is False
    
    def test_valid_sha256_mixed(self):
        """Mixed case should fail."""
        mixed_hash = "a" * 32 + "B" * 32
        assert validate_trace_id_format(mixed_hash) is False
    
    def test_too_short(self):
        """String shorter than 64 chars."""
        short_hash = "a" * 63
        assert validate_trace_id_format(short_hash) is False
    
    def test_too_long(self):
        """String longer than 64 chars."""
        long_hash = "a" * 65
        assert validate_trace_id_format(long_hash) is False
    
    def test_invalid_characters(self):
        """String with non-hex characters."""
        invalid_hash = "g" * 64
        assert validate_trace_id_format(invalid_hash) is False
    
    def test_non_string_input(self):
        """Non-string input."""
        assert validate_trace_id_format(123) is False
        assert validate_trace_id_format(None) is False
        assert validate_trace_id_format(["a" * 64]) is False
    
    def test_empty_string(self):
        """Empty string."""
        assert validate_trace_id_format("") is False
    
    def test_whitespace(self):
        """String with whitespace."""
        assert validate_trace_id_format(" " + "a" * 63) is False
        # But strip should work inside the function? No, regex expects exact match
        # Actually, our regex doesn't strip, but the function calls .strip() on the input
        # Wait, let's check: validate_trace_id_format calls trace_id.strip()
        # So " a...a " should pass
        assert validate_trace_id_format(" " + "a" * 64 + " ") is True

class TestMainFunction:
    """Tests for the main() function of validate_trace_id.py."""
    
    def test_file_not_found(self):
        """Test when file does not exist."""
        # Use a non-existent path
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            # Ensure data/results doesn't exist
            result = main()
            assert result == 0  # Should exit 0 with warning
        os.chdir(original_cwd)
    
    def test_file_empty(self):
        """Test when file exists but is empty."""
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            # Create directory structure
            Path("data/results").mkdir(parents=True)
            # Create empty file
            Path("data/results/network_metrics.csv").touch()
            
            result = main()
            assert result == 0  # Should exit 0 with warning
        os.chdir(original_cwd)
    
    def test_missing_column(self):
        """Test when trace_id column is missing."""
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            Path("data/results").mkdir(parents=True)
            
            # Create CSV without trace_id column
            df = pd.DataFrame({
                'participant_id': ['P1', 'P2'],
                'global_efficiency': [0.5, 0.6]
            })
            df.to_csv("data/results/network_metrics.csv", index=False)
            
            result = main()
            assert result == 1  # Should exit 1 with error
        os.chdir(original_cwd)
    
    def test_all_valid_trace_ids(self):
        """Test when all trace_id values are valid."""
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            Path("data/results").mkdir(parents=True)
            
            # Create CSV with valid trace_ids
            df = pd.DataFrame({
                'participant_id': ['P1', 'P2', 'P3'],
                'global_efficiency': [0.5, 0.6, 0.7],
                'trace_id': ['a' * 64, 'b' * 64, 'c' * 64]
            })
            df.to_csv("data/results/network_metrics.csv", index=False)
            
            result = main()
            assert result == 0  # Should exit 0 with success
        os.chdir(original_cwd)
    
    def test_invalid_trace_ids(self):
        """Test when some trace_id values are invalid."""
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            Path("data/results").mkdir(parents=True)
            
            # Create CSV with one invalid trace_id
            df = pd.DataFrame({
                'participant_id': ['P1', 'P2'],
                'global_efficiency': [0.5, 0.6],
                'trace_id': ['a' * 64, 'invalid']  # 'invalid' is not 64 hex chars
            })
            df.to_csv("data/results/network_metrics.csv", index=False)
            
            result = main()
            assert result == 1  # Should exit 1 with error
        os.chdir(original_cwd)