import os
import tempfile
import pytest
from pathlib import Path
from src.utils import calculate_checksum, ResourceLimitExceeded

class TestCalculateChecksum:
    """Tests for calculate_checksum function."""

    def test_calculate_checksum_valid_file(self):
        """Test checksum calculation on a valid file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Hello, World!")
            temp_path = f.name

        try:
            checksum = calculate_checksum(temp_path)
            assert len(checksum) == 64  # SHA256 hex length
            assert isinstance(checksum, str)
        finally:
            os.unlink(temp_path)

    def test_calculate_checksum_empty_file(self):
        """Test that calculate_checksum raises ValueError on empty file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
            # File is created empty

        try:
            with pytest.raises(ValueError, match="File is empty"):
                calculate_checksum(temp_path)
        finally:
            os.unlink(temp_path)

    def test_calculate_checksum_missing_file(self):
        """Test that calculate_checksum raises FileNotFoundError on missing file."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            calculate_checksum("/nonexistent/path/to/file.txt")

    def test_calculate_checksum_binary_content(self):
        """Test checksum calculation on binary content."""
        binary_data = b"\x00\x01\x02\x03\x04\x05"
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(binary_data)
            temp_path = f.name

        try:
            checksum = calculate_checksum(temp_path)
            assert len(checksum) == 64
        finally:
            os.unlink(temp_path)
