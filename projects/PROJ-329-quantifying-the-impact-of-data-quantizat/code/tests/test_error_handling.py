"""
Tests for error handling utilities in src/error_handling.py.

These tests verify that the pipeline fails gracefully with clear error messages
when noise files are missing, corrupted, or inaccessible.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sys
import hashlib

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.error_handling import (
    NoiseFileError,
    MissingNoiseFileError,
    CorruptedNoiseFileError,
    NoiseFileAccessError,
    get_noise_file_directories,
    find_noise_file,
    calculate_file_checksum,
    validate_noise_file,
    load_noise_file_with_fallback,
    handle_noise_file_error,
    ensure_noise_file_availability
)


class TestNoiseFileValidation:
    """Tests for noise file validation logic."""

    def test_validate_valid_file(self, tmp_path):
        """Test validation of a valid noise file."""
        # Create a fake HDF5 file with correct magic bytes
        file_path = tmp_path / "valid_noise.h5"
        with open(file_path, 'wb') as f:
            f.write(b'\x89HDF')  # HDF5 magic
            f.write(b'\x00' * 100)  # Padding
        
        assert validate_noise_file(file_path) is True

    def test_validate_empty_file(self, tmp_path):
        """Test validation fails for empty file."""
        file_path = tmp_path / "empty_noise.h5"
        file_path.touch()
        
        with pytest.raises(CorruptedNoiseFileError) as exc_info:
            validate_noise_file(file_path)
        
        assert "empty" in str(exc_info.value).lower()

    def test_validate_invalid_header(self, tmp_path):
        """Test validation fails for invalid file header."""
        file_path = tmp_path / "fake_noise.h5"
        with open(file_path, 'wb') as f:
            f.write(b'NOT HDF5 HEADER')
        
        with pytest.raises(CorruptedNoiseFileError) as exc_info:
            validate_noise_file(file_path)
        
        assert "Invalid HDF5 header" in str(exc_info.value)

    def test_validate_checksum_mismatch(self, tmp_path):
        """Test validation fails when checksum doesn't match."""
        file_path = tmp_path / "noise.h5"
        file_path.write_text("data")
        
        wrong_checksum = "a" * 64  # Fake checksum
        
        with pytest.raises(CorruptedNoiseFileError) as exc_info:
            validate_noise_file(file_path, expected_checksum=wrong_checksum)
        
        assert "Checksum mismatch" in str(exc_info.value)

    def test_validate_checksum_match(self, tmp_path):
        """Test validation passes when checksum matches."""
        file_path = tmp_path / "noise.h5"
        file_path.write_text("data")
        
        # Calculate real checksum
        real_checksum = calculate_file_checksum(file_path)
        
        # Should not raise
        assert validate_noise_file(file_path, expected_checksum=real_checksum) is True


class TestChecksumCalculation:
    """Tests for file checksum calculation."""

    def test_calculate_checksum(self, tmp_path):
        """Test checksum calculation for a known file."""
        file_path = tmp_path / "test.txt"
        content = b"Hello, World!"
        file_path.write_bytes(content)
        
        checksum = calculate_file_checksum(file_path)
        
        # Verify against Python's hashlib
        expected = hashlib.sha256(content).hexdigest()
        assert checksum == expected

    def test_calculate_checksum_large_file(self, tmp_path):
        """Test checksum calculation for a large file (chunked reading)."""
        file_path = tmp_path / "large.bin"
        # Create 1MB file
        chunk = b"x" * 65536
        with open(file_path, 'wb') as f:
            for _ in range(16):
                f.write(chunk)
        
        checksum = calculate_file_checksum(file_path)
        assert len(checksum) == 64  # SHA256 hex length
        assert isinstance(checksum, str)


class TestFallbackLoading:
    """Tests for fallback loading behavior."""

    def test_load_nonexistent_strict_true(self):
        """Test that strict=True raises MissingNoiseFileError."""
        with pytest.raises(MissingNoiseFileError) as exc_info:
            load_noise_file_with_fallback("nonexistent.h5", strict=True)
        
        assert "not found" in str(exc_info.value).lower()

    def test_load_nonexistent_strict_false(self):
        """Test that strict=False returns None."""
        result = load_noise_file_with_fallback("nonexistent.h5", strict=False)
        assert result is None

    def test_load_existing_valid(self, tmp_path, monkeypatch):
        """Test loading an existing valid file."""
        # Create a valid noise file
        noise_file = tmp_path / "valid.h5"
        with open(noise_file, 'wb') as f:
            f.write(b'\x89HDF')
            f.write(b'\x00' * 50)
        
        # Monkeypatch the search directory
        monkeypatch.setenv('GW_NOISE_DATA_DIR', str(tmp_path))
        
        result = load_noise_file_with_fallback("valid.h5", strict=True)
        assert result == noise_file


class TestErrorHandling:
    """Tests for error handling and logging."""

    def test_missing_error_attributes(self):
        """Test MissingNoiseFileError stores search paths."""
        paths = ["/a", "/b"]
        try:
            raise MissingNoiseFileError("Not found", search_paths=paths)
        except MissingNoiseFileError as e:
            assert e.search_paths == paths
            assert e.details['search_paths'] == paths

    def test_corrupted_error_attributes(self, tmp_path):
        """Test CorruptedNoiseFileError stores file details."""
        file_path = tmp_path / "bad.h5"
        try:
            raise CorruptedNoiseFileError(
                "Bad file",
                str(file_path),
                "expected",
                "actual"
            )
        except CorruptedNoiseFileError as e:
            assert e.file_path == str(file_path)
            assert e.details['expected_checksum'] == "expected"
            assert e.details['actual_checksum'] == "actual"

    def test_handle_noise_file_error(self, caplog):
        """Test that handle_noise_file_error logs and re-raises."""
        caplog.set_level("ERROR")
        error = MissingNoiseFileError("Test error", search_paths=["/tmp"])
        
        with pytest.raises(MissingNoiseFileError):
            handle_noise_file_error(error)
        
        assert "MISSING NOISE FILE" in caplog.text


class TestDirectoryFunctions:
    """Tests for directory-related functions."""

    def test_get_noise_file_directories_env(self, monkeypatch, tmp_path):
        """Test directory retrieval from environment variable."""
        test_dir = str(tmp_path)
        monkeypatch.setenv('GW_NOISE_DATA_DIR', test_dir)
        
        dirs = get_noise_file_directories()
        assert len(dirs) == 1
        assert dirs[0] == Path(test_dir)

    def test_get_noise_file_directories_default(self, monkeypatch):
        """Test directory retrieval from defaults when env is unset."""
        monkeypatch.delenv('GW_NOISE_DATA_DIR', raising=False)
        
        dirs = get_noise_file_directories()
        assert len(dirs) >= 1
        # Check that default paths are returned
        assert any('data' in str(p) for p in dirs)

    def test_find_file_not_found(self, monkeypatch):
        """Test find_noise_file returns None when not found and required=False."""
        monkeypatch.setenv('GW_NOISE_DATA_DIR', '/nonexistent/path')
        
        result = find_noise_file("fake.h5", required=False)
        assert result is None

    def test_find_file_found(self, tmp_path, monkeypatch):
        """Test find_noise_file returns path when found."""
        noise_file = tmp_path / "found.h5"
        noise_file.touch()
        monkeypatch.setenv('GW_NOISE_DATA_DIR', str(tmp_path))
        
        result = find_noise_file("found.h5", required=True)
        assert result == noise_file


class TestEnsureAvailability:
    """Tests for ensure_noise_file_availability wrapper."""

    def test_ensure_missing_raises(self):
        """Test that ensure raises on missing file."""
        with pytest.raises(MissingNoiseFileError):
            ensure_noise_file_availability("missing.h5")

    def test_ensure_valid_returns_path(self, tmp_path, monkeypatch):
        """Test that ensure returns path for valid file."""
        noise_file = tmp_path / "valid.h5"
        with open(noise_file, 'wb') as f:
            f.write(b'\x89HDF')
        
        monkeypatch.setenv('GW_NOISE_DATA_DIR', str(tmp_path))
        
        result = ensure_noise_file_availability("valid.h5")
        assert result == noise_file
