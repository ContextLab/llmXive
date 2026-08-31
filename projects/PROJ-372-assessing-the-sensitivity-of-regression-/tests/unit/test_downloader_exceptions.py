"""
Unit tests for custom exception classes in downloader module.
"""
import pytest
from pathlib import Path
from src.ingestion.downloader import (
    IngestionError,
    DownloadError,
    ValidationError,
    download_dataset,
)


class TestIngestionError:
    """Tests for the base IngestionError class."""

    def test_ingestion_error_instantiation(self):
        """Test that IngestionError can be instantiated with a message."""
        error = IngestionError("Test error message")
        assert str(error) == "Test error message"

    def test_ingestion_error_subclass(self):
        """Test that IngestionError is a subclass of Exception."""
        assert issubclass(IngestionError, Exception)


class TestDownloadError:
    """Tests for the DownloadError exception class."""

    def test_download_error_basic(self):
        """Test basic DownloadError instantiation."""
        error = DownloadError("Download failed")
        assert error.message == "Download failed"
        assert error.source is None

    def test_download_error_with_source(self):
        """Test DownloadError with source parameter."""
        error = DownloadError("Connection timeout", source="https://example.com")
        assert error.message == "Connection timeout"
        assert error.source == "https://example.com"

    def test_download_error_is_ingestion_error(self):
        """Test that DownloadError is a subclass of IngestionError."""
        assert issubclass(DownloadError, IngestionError)

    def test_download_error_raised_on_missing_source(self):
        """Test that DownloadError is raised when source is missing."""
        with pytest.raises(DownloadError) as exc_info:
            download_dataset(
                dataset_name="test",
                output_dir="/tmp",
                source_url=None,
            )
        assert "Source URL or dataset identifier required" in str(exc_info.value)


class TestValidationError:
    """Tests for the ValidationError exception class."""

    def test_validation_error_basic(self):
        """Test basic ValidationError instantiation."""
        error = ValidationError("Hash mismatch")
        assert error.message == "Hash mismatch"
        assert error.field is None

    def test_validation_error_with_field(self):
        """Test ValidationError with field parameter."""
        error = ValidationError("Invalid column", field="column_name")
        assert error.message == "Invalid column"
        assert error.field == "column_name"

    def test_validation_error_is_ingestion_error(self):
        """Test that ValidationError is a subclass of IngestionError."""
        assert issubclass(ValidationError, IngestionError)