"""
Unit tests for error handling utilities.
"""

import pytest
import sys
import os

# Add the code directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from utils.error_handlers import (
    handle_download_failure,
    handle_memory_error,
    safe_download,
    safe_process_item,
    DownloadError,
    MemoryErrorHandled,
    ValidationError
)


class TestDownloadErrorHandling:
    """Tests for download error handling."""

    def test_catches_download_error(self):
        """Test that handle_download_failure catches and re-raises DownloadError."""
        @handle_download_failure
        def mock_download():
            raise DownloadError("Connection timed out")

        with pytest.raises(DownloadError) as exc_info:
            mock_download()

        assert "Connection timed out" in str(exc_info.value)

    def test_wraps_unexpected_errors_as_download_error(self):
        """Test that unexpected errors during download are wrapped."""
        @handle_download_failure
        def mock_download():
            raise ValueError("Unexpected logic error")

        with pytest.raises(DownloadError) as exc_info:
            mock_download()

        assert "Download failed" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, ValueError)


class TestMemoryErrorHandling:
    """Tests for memory error handling."""

    def test_catches_memory_error(self):
        """Test that handle_memory_error catches MemoryError and raises MemoryErrorHandled."""
        @handle_memory_error
        def mock_process():
            raise MemoryError("RAM exhausted")

        with pytest.raises(MemoryErrorHandled) as exc_info:
            mock_process()

        assert "MemoryError" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, MemoryError)

    def test_allows_other_exceptions_to_pass(self):
        """Test that non-memory exceptions are not caught."""
        @handle_memory_error
        def mock_process():
            raise ValueError("Not a memory error")

        with pytest.raises(ValueError) as exc_info:
            mock_process()

        assert "Not a memory error" in str(exc_info.value)


class TestSafeDownload:
    """Tests for safe_download wrapper."""

    def test_success_path(self):
        """Test successful download path."""
        @safe_download
        def mock_download():
            return "data_file.parquet"

        result = mock_download()
        assert result == "data_file.parquet"

    def test_failure_path(self):
        """Test download failure path."""
        @safe_download
        def mock_download():
            raise Exception("Network failure")

        with pytest.raises(DownloadError):
            mock_download()


class TestSafeProcessItem:
    """Tests for safe_process_item wrapper."""

    def test_success_path(self):
        """Test successful processing path."""
        @safe_process_item
        def mock_process(item):
            return item * 2

        assert mock_process(5) == 10

    def test_memory_error_path(self):
        """Test memory error handling in processing."""
        @safe_process_item
        def mock_process(item):
            raise MemoryError("OOM")

        with pytest.raises(MemoryErrorHandled):
            mock_process(5)


class TestValidationError:
    """Tests for ValidationError custom exception."""

    def test_init_with_message_only(self):
        """Test initialization with just a message."""
        exc = ValidationError("Invalid value")
        assert exc.message == "Invalid value"
        assert exc.field is None
        assert exc.value is None

    def test_init_with_all_args(self):
        """Test initialization with all arguments."""
        exc = ValidationError("Invalid format", field="smiles", value="123")
        assert exc.message == "Invalid format"
        assert exc.field == "smiles"
        assert exc.value == "123"

    def test_str_representation(self):
        """Test string representation."""
        exc = ValidationError("Error message")
        assert "Error message" in str(exc)