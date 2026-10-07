"""
Unit tests for error handling utilities in code/utils/error_handlers.py.

These tests verify that MemoryError and DownloadError are caught explicitly
and that no synthetic fallbacks are used.
"""

import pytest
import logging
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure the 'code' directory is in the path for imports
sys.path.insert(0, os.path.join(os.dirname(__file__), '..', '..'))

from utils.error_handlers import (
    handle_download_failure,
    handle_memory_error,
    safe_download,
    safe_process_item,
    DownloadError,
    MemoryErrorHandled,
    main
)


class TestHandleDownloadFailure:
    """Tests for the handle_download_failure decorator."""

    def test_catches_download_error(self):
        """Test that DownloadError is caught and re-raised."""
        @handle_download_failure
        def mock_download():
            raise DownloadError("Network timeout")

        with pytest.raises(DownloadError, match="Network timeout"):
            mock_download()

    def test_wraps_other_errors_as_download_error(self):
        """Test that unexpected errors are wrapped in DownloadError."""
        @handle_download_failure
        def mock_failing_download():
            raise ValueError("Unexpected logic error")

        with pytest.raises(DownloadError, match="Unexpected error during download"):
            mock_failing_download()

    def test_logs_download_error(self):
        """Test that DownloadError is logged correctly."""
        with patch('utils.error_handlers.log_event') as mock_log:
            @handle_download_failure
            def mock_download():
                raise DownloadError("Test error")

            try:
                mock_download()
            except DownloadError:
                pass

            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            assert args[1] == "ERROR"
            assert "Download failed" in args[2]


class TestHandleMemoryError:
    """Tests for the handle_memory_error decorator."""

    def test_catches_memory_error(self):
        """Test that MemoryError is caught and raised as MemoryErrorHandled."""
        @handle_memory_error
        def mock_process():
            raise MemoryError("Out of memory")

        with pytest.raises(MemoryErrorHandled, match="MemoryError caught"):
            mock_process()

    def test_logs_memory_error(self):
        """Test that MemoryError is logged correctly."""
        with patch('utils.error_handlers.log_event') as mock_log:
            @handle_memory_error
            def mock_process():
                raise MemoryError("Test memory error")

            try:
                mock_process()
            except MemoryErrorHandled:
                pass

            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            assert args[1] == "ERROR"
            assert "MemoryError handled" in args[2]

    def test_allows_other_errors(self):
        """Test that non-MemoryError exceptions are not caught."""
        @handle_memory_error
        def mock_process():
            raise ValueError("Regular error")

        with pytest.raises(ValueError, match="Regular error"):
            mock_process()


class TestSafeDownload:
    """Tests for the safe_download wrapper."""

    def test_logs_start_and_success(self):
        """Test that successful download logs start and end."""
        with patch('utils.error_handlers.logger') as mock_logger:
            @safe_download
            def mock_download():
                return "data"

            result = mock_download()

            assert result == "data"
            assert mock_logger.info.call_count >= 2

    def test_raises_download_error_on_failure(self):
        """Test that DownloadError is raised on failure."""
        @safe_download
        def mock_failing_download():
            raise DownloadError("Failed")

        with pytest.raises(DownloadError):
            mock_failing_download()

    def test_wraps_unexpected_error(self):
        """Test that unexpected errors are wrapped in DownloadError."""
        @safe_download
        def mock_failing_download():
            raise KeyError("Unexpected")

        with pytest.raises(DownloadError, match="Download failed"):
            mock_failing_download()


class TestSafeProcessItem:
    """Tests for the safe_process_item wrapper."""

    def test_catches_memory_error(self):
        """Test that MemoryError is caught and raised as MemoryErrorHandled."""
        @safe_process_item
        def mock_process():
            raise MemoryError("Memory limit")

        with pytest.raises(MemoryErrorHandled):
            mock_process()

    def test_allows_normal_execution(self):
        """Test that normal execution returns result."""
        @safe_process_item
        def mock_process():
            return "processed"

        assert mock_process() == "processed"


class TestMain:
    """Tests for the main entry point."""

    def test_runs_without_error(self):
        """Test that main() runs without raising unhandled exceptions."""
        # Capture logs to ensure no errors occur
        with patch('utils.error_handlers.logger') as mock_logger:
            # We expect the function to run and catch errors internally
            main()
            # Verify that the "Error handler tests completed" message was logged
            mock_logger.info.assert_any_call("Error handler tests completed.")