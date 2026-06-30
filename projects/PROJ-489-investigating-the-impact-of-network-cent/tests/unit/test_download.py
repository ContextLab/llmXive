"""
Unit tests for checksum verification in download.py.
Specifically tests the integration with integrity.py for checksum validation.
"""
import json
import os
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

import pytest

# Import the integrity module which handles checksum logic
# Note: download.py uses integrity.py for checksum verification
from integrity import calculate_file_checksum, verify_manifest


class TestChecksumVerification:
    """Tests for file checksum calculation and verification."""

    def test_calculate_file_checksum_md5(self):
        """Test that calculate_file_checksum correctly computes MD5 hash."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Hello, World!")
            temp_path = f.name

        try:
            checksum = calculate_file_checksum(temp_path, algorithm='md5')
            expected = hashlib.md5(b"Hello, World!").hexdigest()
            assert checksum == expected, f"Expected {expected}, got {checksum}"
        finally:
            os.unlink(temp_path)

    def test_calculate_file_checksum_sha256(self):
        """Test that calculate_file_checksum correctly computes SHA256 hash."""
        test_data = b"Test data for SHA256"
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.bin') as f:
            f.write(test_data)
            temp_path = f.name

        try:
            checksum = calculate_file_checksum(temp_path, algorithm='sha256')
            expected = hashlib.sha256(test_data).hexdigest()
            assert checksum == expected, f"Expected {expected}, got {checksum}"
        finally:
            os.unlink(temp_path)

    def test_calculate_file_checksum_invalid_algorithm(self):
        """Test that invalid algorithm raises ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test")
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                calculate_file_checksum(temp_path, algorithm='invalid_algo')
        finally:
            os.unlink(temp_path)

    def test_verify_manifest_success(self):
        """Test successful verification when checksums match."""
        # Create a temporary directory with a file
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.edf"
            test_file.write_text("Mock EDF content")
            
            # Calculate correct checksum
            correct_checksum = calculate_file_checksum(str(test_file), 'md5')
            
            # Create manifest
            manifest = {
                "files": {
                    "test.edf": {
                        "checksum": correct_checksum,
                        "algorithm": "md5"
                    }
                }
            }
            
            manifest_path = Path(tmpdir) / "manifest.json"
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f)
            
            # Verify should return True
            result = verify_manifest(str(manifest_path), tmpdir)
            assert result is True

    def test_verify_manifest_mismatch(self):
        """Test verification failure when checksums do not match."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.edf"
            test_file.write_text("Mock EDF content")
            
            # Create manifest with WRONG checksum
            wrong_checksum = "00000000000000000000000000000000"
            manifest = {
                "files": {
                    "test.edf": {
                        "checksum": wrong_checksum,
                        "algorithm": "md5"
                    }
                }
            }
            
            manifest_path = Path(tmpdir) / "manifest.json"
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f)
            
            # Verify should return False
            result = verify_manifest(str(manifest_path), tmpdir)
            assert result is False

    def test_verify_manifest_missing_file(self):
        """Test verification failure when file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create manifest referencing a non-existent file
            manifest = {
                "files": {
                    "missing.edf": {
                        "checksum": "some_checksum",
                        "algorithm": "md5"
                    }
                }
            }
            
            manifest_path = Path(tmpdir) / "manifest.json"
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f)
            
            # Verify should return False
            result = verify_manifest(str(manifest_path), tmpdir)
            assert result is False

    @patch('integrity.calculate_file_checksum')
    @patch('integrity.Path')
    def test_verify_manifest_integration_path(self, mock_path, mock_calc):
        """Test verify_manifest logic with mocked checksum calculation."""
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True
        mock_path_instance.is_file.return_value = True
        mock_path_instance.name = "test.edf"
        
        # Mock the checksum to return a specific value
        mock_calc.return_value = "abc123"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = {
                "files": {
                    "test.edf": {
                        "checksum": "abc123",
                        "algorithm": "md5"
                    }
                }
            }
            
            manifest_path = Path(tmpdir) / "manifest.json"
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f)
            
            result = verify_manifest(str(manifest_path), tmpdir)
            assert result is True
            mock_calc.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])