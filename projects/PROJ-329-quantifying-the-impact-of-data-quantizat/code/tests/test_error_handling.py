"""
Tests for error handling module.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sys
import json

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from src.error_handling import (
    NoiseFileError,
    MissingNoiseFileError,
    CorruptedNoiseFileError,
    NoiseFileAccessError,
    validate_noise_file,
    calculate_file_checksum,
    load_noise_file_with_fallback,
    handle_noise_file_error,
    get_noise_file_directories,
    find_noise_file,
    ensure_noise_file_availability
)


class TestNoiseFileValidation:
    """Test noise file validation functions."""

    def test_validate_existing_valid_file(self, tmp_path):
        """Test validation of an existing, valid file."""
        # Create a valid text file
        test_file = tmp_path / "valid_noise.txt"
        test_file.write_text("1.0\n2.0\n3.0\n")
        
        is_valid, msg = validate_noise_file(str(test_file))
        assert is_valid
        assert "successful" in msg.lower()

    def test_validate_empty_file(self, tmp_path):
        """Test validation fails for empty file."""
        # Create an empty file
        test_file = tmp_path / "empty_noise.txt"
        test_file.write_text("")
        
        with pytest.raises(CorruptedNoiseFileError) as exc_info:
            validate_noise_file(str(test_file))
        
        assert "empty" in str(exc_info.value).lower()

    def test_validate_nonexistent_file(self, tmp_path):
        """Test validation fails for non-existent file."""
        fake_path = tmp_path / "does_not_exist.txt"
        
        with pytest.raises(MissingNoiseFileError):
            validate_noise_file(str(fake_path))

    def test_validate_checksum_mismatch(self, tmp_path):
        """Test validation fails when checksum doesn't match."""
        test_file = tmp_path / "noise.txt"
        test_file.write_text("test data")
        
        wrong_checksum = "0" * 64  # Invalid checksum
        
        with pytest.raises(CorruptedNoiseFileError) as exc_info:
            validate_noise_file(str(test_file), expected_checksum=wrong_checksum)
        
        assert "checksum" in str(exc_info.value).lower()


class TestChecksumCalculation:
    """Test checksum calculation functions."""

    def test_calculate_checksum(self, tmp_path):
        """Test checksum calculation for a file."""
        test_file = tmp_path / "test.txt"
        content = "test content for checksum"
        test_file.write_text(content)
        
        checksum = calculate_file_checksum(str(test_file))
        
        # Verify it's a valid SHA-256 hex string
        assert len(checksum) == 64
        assert all(c in '0123456789abcdef' for c in checksum)

    def test_calculate_checksum_consistency(self, tmp_path):
        """Test that checksum is consistent for same file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        checksum1 = calculate_file_checksum(str(test_file))
        checksum2 = calculate_file_checksum(str(test_file))
        
        assert checksum1 == checksum2

    def test_calculate_checksum_nonexistent(self, tmp_path):
        """Test checksum fails for non-existent file."""
        fake_path = tmp_path / "nonexistent.txt"
        
        with pytest.raises(MissingNoiseFileError):
            calculate_file_checksum(str(fake_path))


class TestFallbackLoading:
    """Test fallback loading mechanisms."""

    def test_load_valid_file(self, tmp_path):
        """Test loading a valid file."""
        test_file = tmp_path / "noise.txt"
        test_file.write_text("data")
        
        path, error = load_noise_file_with_fallback(str(test_file))
        
        assert path is not None
        assert error is None
        assert path.exists()

    def test_load_missing_file(self, tmp_path):
        """Test loading a missing file returns error."""
        fake_path = tmp_path / "nonexistent.txt"
        
        path, error = load_noise_file_with_fallback(str(fake_path))
        
        assert path is None
        assert error is not None
        assert isinstance(error, MissingNoiseFileError)

    def test_load_corrupted_file(self, tmp_path):
        """Test loading a corrupted (empty) file returns error."""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")
        
        path, error = load_noise_file_with_fallback(str(test_file))
        
        assert path is None
        assert error is not None
        assert isinstance(error, CorruptedNoiseFileError)


class TestErrorHandling:
    """Test error handling and reporting."""

    def test_handle_missing_error(self):
        """Test handling of missing file error."""
        error = MissingNoiseFileError("test.txt", ["/path1", "/path2"])
        result = handle_noise_file_error(error)
        
        assert result["success"] is False
        assert result["error_category"] == "missing"
        assert "MissingNoiseFileError" in result["error_type"]

    def test_handle_corrupted_error(self):
        """Test handling of corrupted file error."""
        error = CorruptedNoiseFileError("test.txt", "Checksum mismatch")
        result = handle_noise_file_error(error)
        
        assert result["success"] is False
        assert result["error_category"] == "corrupted"

    def test_handle_access_error(self):
        """Test handling of access error."""
        error = NoiseFileAccessError("test.txt", "Permission denied")
        result = handle_noise_file_error(error)
        
        assert result["success"] is False
        assert result["error_category"] == "access"

    def test_handle_unknown_error(self):
        """Test handling of unknown error type."""
        error = ValueError("Some unknown error")
        result = handle_noise_file_error(error)
        
        assert result["success"] is False
        assert result["error_category"] == "unknown"


class TestDirectoryFunctions:
    """Test directory-related functions."""

    def test_get_noise_file_directories(self):
        """Test getting noise file directories."""
        dirs = get_noise_file_directories()
        
        # Should return a list
        assert isinstance(dirs, list)
        # Should contain Path objects
        assert all(isinstance(d, Path) for d in dirs)

    def test_find_noise_file_existing(self, tmp_path, monkeypatch):
        """Test finding an existing noise file."""
        # Create a noise file in a standard location
        noise_dir = tmp_path / "data" / "raw" / "noise"
        noise_dir.mkdir(parents=True)
        test_file = noise_dir / "test_noise.txt"
        test_file.write_text("data")
        
        # Mock the project root
        monkeypatch.setenv('PROJECT_ROOT', str(tmp_path))
        
        found = find_noise_file("test_noise.txt")
        
        assert found is not None
        assert found.exists()

    def test_find_noise_file_missing(self, tmp_path, monkeypatch):
        """Test finding a missing noise file."""
        monkeypatch.setenv('PROJECT_ROOT', str(tmp_path))
        
        found = find_noise_file("nonexistent.txt")
        
        assert found is None


class TestEnsureAvailability:
    """Test ensure_noise_file_availability function."""

    def test_ensure_existing_valid(self, tmp_path, monkeypatch):
        """Test ensuring availability of existing valid file."""
        noise_dir = tmp_path / "data" / "raw" / "noise"
        noise_dir.mkdir(parents=True)
        test_file = noise_dir / "valid.txt"
        test_file.write_text("data")
        
        monkeypatch.setenv('PROJECT_ROOT', str(tmp_path))
        
        result = ensure_noise_file_availability("valid.txt")
        
        assert result.exists()
        assert result == test_file

    def test_ensure_missing(self, tmp_path, monkeypatch):
        """Test ensuring availability fails for missing file."""
        monkeypatch.setenv('PROJECT_ROOT', str(tmp_path))
        
        with pytest.raises(MissingNoiseFileError):
            ensure_noise_file_availability("nonexistent.txt")

    def test_ensure_corrupted(self, tmp_path, monkeypatch):
        """Test ensuring availability fails for corrupted file."""
        noise_dir = tmp_path / "data" / "raw" / "noise"
        noise_dir.mkdir(parents=True)
        test_file = noise_dir / "empty.txt"
        test_file.write_text("")
        
        monkeypatch.setenv('PROJECT_ROOT', str(tmp_path))
        
        with pytest.raises(CorruptedNoiseFileError):
            ensure_noise_file_availability("empty.txt")