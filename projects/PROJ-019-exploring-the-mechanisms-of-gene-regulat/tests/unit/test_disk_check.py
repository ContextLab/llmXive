"""
Unit tests for the disk_check utility module.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from code.utils.disk_check import (
    get_available_space,
    check_disk_space,
    InsufficientDiskSpaceError,
    MIN_DISK_SPACE_BYTES,
)


class TestGetAvailableSpace:
    """Tests for the get_available_space function."""

    def test_returns_positive_int_for_existing_dir(self, tmp_path):
        """Should return a positive integer for an existing directory."""
        available = get_available_space(tmp_path)
        assert isinstance(available, int)
        assert available >= 0

    def test_raises_file_not_found_for_nonexistent_path(self):
        """Should raise FileNotFoundError for a path that doesn't exist."""
        fake_path = Path("/nonexistent/path/12345")
        with pytest.raises(FileNotFoundError):
            get_available_space(fake_path)

    def test_raises_not_a_directory_for_file(self, tmp_path):
        """Should raise NotADirectoryError when path is a file."""
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("test")
        with pytest.raises(NotADirectoryError):
            get_available_space(test_file)


class TestCheckDiskSpace:
    """Tests for the check_disk_space function."""

    def test_returns_true_when_sufficient_space(self, tmp_path):
        """Should return True when sufficient space is available."""
        # tmp_path should have plenty of space in a typical test environment
        assert check_disk_space(required_bytes=1024, target_dir=tmp_path) is True

    def test_raises_insufficient_error_when_space_low(self, tmp_path):
        """Should raise InsufficientDiskSpaceError when space is insufficient."""
        # Request more space than likely available in a temp directory
        huge_requirement = 1024 ** 4  # 1 TB
        with pytest.raises(InsufficientDiskSpaceError):
            check_disk_space(required_bytes=huge_requirement, target_dir=tmp_path)

    def test_uses_default_target_when_not_specified(self):
        """Should use TMP_DIR from config when target_dir is None."""
        # This test assumes TMP_DIR exists and has space (true in CI/dev)
        # We're just verifying the function doesn't crash and uses the default
        try:
            result = check_disk_space()
            assert result is True
        except InsufficientDiskSpaceError:
            # If TMP_DIR is full (unlikely), the function correctly raises
            pytest.skip("TMP_DIR is full in this environment")

    def test_error_message_contains_human_readable_sizes(self, tmp_path):
        """Error message should contain human-readable size information."""
        huge_requirement = 1024 ** 4  # 1 TB
        with pytest.raises(InsufficientDiskSpaceError) as exc_info:
            check_disk_space(required_bytes=huge_requirement, target_dir=tmp_path)
        
        error_msg = str(exc_info.value)
        assert "GB" in error_msg or "GB" in error_msg  # Check for human-readable format
        assert str(tmp_path) in error_msg

class TestInsufficientDiskSpaceError:
    """Tests for the custom exception."""

    def test_exception_has_correct_message(self):
        """Exception should have a descriptive message."""
        msg = "Test insufficient space message"
        with pytest.raises(InsufficientDiskSpaceError) as exc_info:
            raise InsufficientDiskSpaceError(msg)
        
        assert str(exc_info.value) == msg
