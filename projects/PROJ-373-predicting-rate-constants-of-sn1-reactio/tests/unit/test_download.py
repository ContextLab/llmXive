"""
Unit tests for code/data/download.py
"""
import pytest
from pathlib import Path
import tempfile
import os
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.download import check_schema_pass

class TestSchemaPassCheck:
    def test_schema_log_missing(self, tmp_path):
        """Test that check_schema_pass returns False if log is missing."""
        fake_log = tmp_path / "schema_check.log"
        assert check_schema_pass(fake_log) is False

    def test_schema_log_empty(self, tmp_path):
        """Test that check_schema_pass returns False if log is empty."""
        fake_log = tmp_path / "schema_check.log"
        fake_log.write_text("")
        assert check_schema_pass(fake_log) is False

    def test_schema_log_success(self, tmp_path):
        """Test that check_schema_pass returns True if log indicates success."""
        fake_log = tmp_path / "schema_check.log"
        fake_log.write_text("Validation passed\nSome other info")
        assert check_schema_pass(fake_log) is True

    def test_schema_log_failure(self, tmp_path):
        """Test that check_schema_pass returns False if log indicates failure."""
        fake_log = tmp_path / "schema_check.log"
        fake_log.write_text("Validation failed\nError details")
        assert check_schema_pass(fake_log) is False
