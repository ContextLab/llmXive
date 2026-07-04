import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.data.download import calculate_sha256, verify_checksum, log_data_version
from src.data.schema import DataVersionFile

class TestChecksumCalculation:
    def test_calculate_sha256(self):
        """Test SHA256 calculation on a known string."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test data")
            temp_path = Path(f.name)
        
        try:
            checksum = calculate_sha256(temp_path)
            # SHA256 of "test data"
            expected = "916f0f7500f95292e21000137441155809040603090600000000000000000000" # Placeholder, actual hash needed
            # Correct hash for "test data"
            import hashlib
            expected = hashlib.sha256(b"test data").hexdigest()
            
            assert checksum == expected
        finally:
            os.unlink(temp_path)

    def test_verify_checksum_match(self):
        """Test checksum verification when it matches."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test data")
            temp_path = Path(f.name)
        
        try:
            checksum = calculate_sha256(temp_path)
            assert verify_checksum(temp_path, checksum) is True
        finally:
            os.unlink(temp_path)

    def test_verify_checksum_mismatch(self):
        """Test checksum verification when it doesn't match."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test data")
            temp_path = Path(f.name)
        
        try:
            assert verify_checksum(temp_path, "wrong_checksum") is False
        finally:
            os.unlink(temp_path)

class TestDataVersionLogging:
    def test_log_data_version_creates_file(self):
        """Test that log_data_version creates the file if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "data_version.json"
            version_info = [
                DataVersionFile(
                    source_url="http://example.com/data1",
                    checksum_sha256="abc123",
                    timestamp="2023-01-01T00:00:00+00:00"
                )
            ]
            
            result_path = log_data_version(version_info, output_path)
            
            assert result_path.exists()
            with open(result_path, "r") as f:
                data = json.load(f)
            
            assert len(data) == 1
            assert data[0]["source_url"] == "http://example.com/data1"

    def test_log_data_version_appends(self):
        """Test that log_data_version appends to existing data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "data_version.json"
            
            # Create initial file
            initial_data = [
                {
                    "source_url": "http://example.com/existing",
                    "checksum_sha256": "def456",
                    "timestamp": "2023-01-01T00:00:00+00:00"
                }
            ]
            with open(output_path, "w") as f:
                json.dump(initial_data, f)
            
            new_version_info = [
                DataVersionFile(
                    source_url="http://example.com/new",
                    checksum_sha256="ghi789",
                    timestamp="2023-01-02T00:00:00+00:00"
                )
            ]
            
            log_data_version(new_version_info, output_path)
            
            with open(output_path, "r") as f:
                data = json.load(f)
            
            assert len(data) == 2
            assert data[1]["source_url"] == "http://example.com/new"

    def test_log_data_version_no_duplicates(self):
        """Test that log_data_version doesn't add duplicates based on source_url."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "data_version.json"
            
            initial_data = [
                {
                    "source_url": "http://example.com/existing",
                    "checksum_sha256": "def456",
                    "timestamp": "2023-01-01T00:00:00+00:00"
                }
            ]
            with open(output_path, "w") as f:
                json.dump(initial_data, f)
            
            # Try to add the same URL again
            new_version_info = [
                DataVersionFile(
                    source_url="http://example.com/existing",
                    checksum_sha256="new_checksum",
                    timestamp="2023-01-02T00:00:00+00:00"
                )
            ]
            
            log_data_version(new_version_info, output_path)
            
            with open(output_path, "r") as f:
                data = json.load(f)
            
            # Should still be 1 entry
            assert len(data) == 1
            # Checksum should remain the original one (no overwrite)
            assert data[0]["checksum_sha256"] == "def456"