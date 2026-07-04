"""
Unit tests for the logging infrastructure in src/main.py.
"""
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest


# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestLoggingInfrastructure:
    """Tests for the logging infrastructure in main.py."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a temporary directory for test data
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.temp_dir, 'data')
        os.makedirs(self.data_dir, exist_ok=True)

        # Patch the project_root in main module
        import main
        original_project_root = main.project_root
        main.project_root = self.temp_dir

        # Clear any existing data_version.json
        self.version_file = os.path.join(self.data_dir, 'data_version.json')
        if os.path.exists(self.version_file):
            os.remove(self.version_file)

        self.main = main
        self.main.project_root = self.temp_dir

    def teardown_method(self):
        """Clean up test fixtures."""
        import main
        # Restore original project_root
        if hasattr(self, 'original_project_root'):
            main.project_root = self.original_project_root
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_ensure_data_directory_creates_folder(self):
        """Test that ensure_data_directory creates the data folder."""
        # Remove data dir if it exists
        if os.path.exists(self.data_dir):
            os.rmdir(self.data_dir)

        result = self.main.ensure_data_directory()
        assert os.path.isdir(result)
        assert result == self.data_dir

    def test_get_data_version_path(self):
        """Test that get_data_version_path returns correct path."""
        result = self.main.get_data_version_path()
        expected = os.path.join(self.data_dir, 'data_version.json')
        assert result == expected

    def test_load_data_version_returns_empty_dict_when_missing(self):
        """Test loading when file doesn't exist."""
        result = self.main.load_data_version()
        assert result == {}

    def test_load_data_version_returns_empty_dict_when_empty(self):
        """Test loading when file is empty."""
        with open(self.version_file, 'w') as f:
            f.write('')
        result = self.main.load_data_version()
        assert result == {}

    def test_load_data_version_parses_valid_json(self):
        """Test loading valid JSON data."""
        test_data = {"key1": {"source_url": "url1", "checksum_sha256": "hash1", "timestamp": "2023-01-01"}}
        with open(self.version_file, 'w') as f:
            json.dump(test_data, f)

        result = self.main.load_data_version()
        assert result == test_data

    def test_log_data_version_creates_entry(self):
        """Test that log_data_version creates a new entry."""
        result = self.main.log_data_version(
            source_url="https://example.com/data",
            checksum_sha256="abc123",
            description="Test data"
        )

        assert len(result) == 1
        key = "https://example.com/data:abc123"
        assert key in result
        assert result[key]["source_url"] == "https://example.com/data"
        assert result[key]["checksum_sha256"] == "abc123"
        assert "timestamp" in result[key]
        assert result[key]["description"] == "Test data"

    def test_log_data_version_uses_utc_timestamp(self):
        """Test that timestamps are in UTC."""
        result = self.main.log_data_version(
            source_url="https://example.com/data",
            checksum_sha256="abc123"
        )

        key = "https://example.com/data:abc123"
        timestamp = result[key]["timestamp"]
        assert "Z" in timestamp or "+00:00" in timestamp or timestamp.endswith("Z")

    def test_log_data_version_does_not_duplicate_existing_entry(self):
        """Test that logging the same version twice doesn't create duplicates."""
        self.main.log_data_version(
            source_url="https://example.com/data",
            checksum_sha256="abc123"
        )

        result = self.main.log_data_version(
            source_url="https://example.com/data",
            checksum_sha256="abc123"
        )

        assert len(result) == 1

    def test_save_data_version_writes_json(self):
        """Test that save_data_version writes valid JSON."""
        test_data = {
            "key1": {
                "source_url": "url1",
                "checksum_sha256": "hash1",
                "timestamp": "2023-01-01T00:00:00+00:00"
            }
        }

        self.main.save_data_version(test_data)

        assert os.path.exists(self.version_file)
        with open(self.version_file, 'r') as f:
            loaded = json.load(f)
        assert loaded == test_data

    def test_log_pipeline_start_returns_run_id(self):
        """Test that log_pipeline_start returns a run ID."""
        run_id = self.main.log_pipeline_start("test_pipeline")
        assert isinstance(run_id, str)
        assert "test_pipeline" in run_id

    def test_log_pipeline_end_prints_status(self):
        """Test that log_pipeline_end prints status message."""
        # This test mainly ensures the function doesn't crash
        self.main.log_pipeline_end("test_run_123", True, 10.5)
        self.main.log_pipeline_end("test_run_456", False, 5.2)