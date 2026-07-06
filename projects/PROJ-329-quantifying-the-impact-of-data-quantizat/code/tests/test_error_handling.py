"""
Tests for error handling utilities in error_handling.py.

These tests verify that missing and corrupted noise files are handled
gracefully with appropriate error messages and exceptions.
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.error_handling import (
    validate_noise_file,
    calculate_file_checksum,
    load_noise_file_with_fallback,
    handle_noise_file_error,
    get_noise_file_directories,
    find_noise_file,
    ensure_noise_file_availability,
    MissingNoiseFileError,
    CorruptedNoiseFileError,
    NoiseFileAccessError
)

class TestNoiseFileValidation:
    """Tests for noise file validation functions."""
    
    def test_validate_existing_valid_file(self, tmp_path):
        """Test validation of a valid noise file."""
        noise_file = tmp_path / "noise.h5"
        noise_file.write_bytes(b"x" * 2048)  # Create a file > 1KB
        
        is_valid, error_msg = validate_noise_file(str(noise_file))
        
        assert is_valid is True
        assert error_msg == ""
    
    def test_validate_missing_file(self, tmp_path):
        """Test validation of a missing file."""
        non_existent = tmp_path / "does_not_exist.h5"
        
        is_valid, error_msg = validate_noise_file(str(non_existent))
        
        assert is_valid is False
        assert "not found" in error_msg.lower()
    
    def test_validate_directory_instead_of_file(self, tmp_path):
        """Test validation when path is a directory."""
        dir_path = tmp_path / "not_a_file"
        dir_path.mkdir()
        
        is_valid, error_msg = validate_noise_file(str(dir_path))
        
        assert is_valid is False
        assert "not a file" in error_msg.lower()
    
    def test_validate_file_too_small(self, tmp_path):
        """Test validation of a file that's too small."""
        small_file = tmp_path / "small_noise.h5"
        small_file.write_bytes(b"x" * 100)  # 100 bytes < 1024 min
        
        is_valid, error_msg = validate_noise_file(str(small_file))
        
        assert is_valid is False
        assert "too small" in error_msg.lower()
    
    def test_validate_checksum_mismatch(self, tmp_path):
        """Test validation with incorrect checksum."""
        noise_file = tmp_path / "noise.h5"
        noise_file.write_bytes(b"x" * 2048)
        
        wrong_checksum = "a" * 32  # Invalid MD5 format
        
        is_valid, error_msg = validate_noise_file(
            str(noise_file), 
            expected_checksum=wrong_checksum
        )
        
        assert is_valid is False
        assert "checksum mismatch" in error_msg.lower()
    
    def test_validate_correct_checksum(self, tmp_path):
        """Test validation with correct checksum."""
        noise_file = tmp_path / "noise.h5"
        noise_file.write_bytes(b"x" * 2048)
        
        actual_checksum = calculate_file_checksum(noise_file)
        
        is_valid, error_msg = validate_noise_file(
            str(noise_file),
            expected_checksum=actual_checksum
        )
        
        assert is_valid is True
        assert error_msg == ""

class TestChecksumCalculation:
    """Tests for checksum calculation."""
    
    def test_calculate_checksum(self, tmp_path):
        """Test basic checksum calculation."""
        test_file = tmp_path / "test.bin"
        content = b"test content for checksum"
        test_file.write_bytes(content)
        
        checksum = calculate_file_checksum(test_file)
        
        assert len(checksum) == 32  # MD5 hex length
        assert isinstance(checksum, str)
    
    def test_calculate_checksum_nonexistent(self, tmp_path):
        """Test checksum calculation on non-existent file."""
        non_existent = tmp_path / "missing.bin"
        
        with pytest.raises(NoiseFileAccessError):
            calculate_file_checksum(non_existent)

class TestFallbackLoading:
    """Tests for fallback file loading."""
    
    def test_load_primary_file(self, tmp_path):
        """Test loading when primary file exists."""
        primary = tmp_path / "primary_noise.h5"
        primary.write_bytes(b"x" * 2048)
        
        valid_path, error = load_noise_file_with_fallback(str(primary))
        
        assert valid_path == primary
        assert error is None
    
    def test_load_fallback_when_primary_missing(self, tmp_path):
        """Test fallback loading when primary is missing."""
        primary = tmp_path / "primary_noise.h5"
        fallback = tmp_path / "fallback_noise.h5"
        fallback.write_bytes(b"x" * 2048)
        
        valid_path, error = load_noise_file_with_fallback(
            str(primary),
            fallback_path=str(fallback)
        )
        
        assert valid_path == fallback
        assert error is None
    
    def test_load_fails_when_both_missing(self, tmp_path):
        """Test failure when both primary and fallback are missing."""
        primary = tmp_path / "primary_noise.h5"
        fallback = tmp_path / "fallback_noise.h5"
        
        valid_path, error = load_noise_file_with_fallback(
            str(primary),
            fallback_path=str(fallback)
        )
        
        assert valid_path is None
        assert error is not None
        assert "Failed to load noise file" in error

class TestErrorHandling:
    """Tests for error handling functions."""
    
    def test_handle_missing_file_raises(self, tmp_path):
        """Test that missing file raises exception."""
        non_existent = tmp_path / "missing.h5"
        
        with pytest.raises(MissingNoiseFileError):
            handle_noise_file_error(str(non_existent), raise_on_failure=True)
    
    def test_handle_missing_file_returns_false(self, tmp_path):
        """Test that missing file returns False when not raising."""
        non_existent = tmp_path / "missing.h5"
        
        result = handle_noise_file_error(
            str(non_existent),
            raise_on_failure=False
        )
        
        assert result is False
    
    def test_handle_valid_file_returns_true(self, tmp_path):
        """Test that valid file returns True."""
        valid_file = tmp_path / "valid.h5"
        valid_file.write_bytes(b"x" * 2048)
        
        result = handle_noise_file_error(str(valid_file))
        
        assert result is True

class TestDirectoryFunctions:
    """Tests for directory-related functions."""
    
    def test_get_noise_file_directories(self):
        """Test that default directories are returned."""
        dirs = get_noise_file_directories()
        
        assert 'raw' in dirs
        assert 'processed' in dirs
        assert 'fallback' in dirs
        assert isinstance(dirs['raw'], Path)
    
    def test_find_noise_file_returns_none_when_missing(self, tmp_path):
        """Test find_noise_file returns None when no files found."""
        # Create empty directories
        for subdir in ['raw', 'processed', 'fallback']:
            (tmp_path / subdir).mkdir(parents=True)
        
        # Temporarily override the base directory
        import src.error_handling as eh
        original_get_dirs = eh.get_noise_file_directories
        
        def mock_get_dirs():
            return {
                'raw': tmp_path / 'raw',
                'processed': tmp_path / 'processed',
                'fallback': tmp_path / 'fallback'
            }
        
        eh.get_noise_file_directories = mock_get_dirs
        
        try:
            result = find_noise_file(['*.h5'])
            assert result is None
        finally:
            eh.get_noise_file_directories = original_get_dirs

class TestEnsureAvailability:
    """Tests for ensure_noise_file_availability."""
    
    def test_raises_when_no_file_found(self, tmp_path):
        """Test that exception is raised when no file found."""
        # Create empty directories
        for subdir in ['raw', 'processed', 'fallback']:
            (tmp_path / subdir).mkdir(parents=True)
        
        import src.error_handling as eh
        original_get_dirs = eh.get_noise_file_directories
        
        def mock_get_dirs():
            return {
                'raw': tmp_path / 'raw',
                'processed': tmp_path / 'processed',
                'fallback': tmp_path / 'fallback'
            }
        
        eh.get_noise_file_directories = mock_get_dirs
        
        try:
            with pytest.raises(MissingNoiseFileError):
                ensure_noise_file_availability(['*.h5'], error_context="test")
        finally:
            eh.get_noise_file_directories = original_get_dirs
    
    def test_returns_file_when_found(self, tmp_path):
        """Test that file path is returned when found."""
        raw_dir = tmp_path / "raw" / "ligo_noise"
        raw_dir.mkdir(parents=True)
        
        noise_file = raw_dir / "O3_noise.h5"
        noise_file.write_bytes(b"x" * 2048)
        
        import src.error_handling as eh
        original_get_dirs = eh.get_noise_file_directories
        
        def mock_get_dirs():
            return {
                'raw': raw_dir,
                'processed': tmp_path / 'processed',
                'fallback': tmp_path / 'fallback'
            }
        
        eh.get_noise_file_directories = mock_get_dirs
        
        try:
            result = ensure_noise_file_availability(['*.h5'], error_context="test")
            assert result == noise_file
        finally:
            eh.get_noise_file_directories = original_get_dirs
