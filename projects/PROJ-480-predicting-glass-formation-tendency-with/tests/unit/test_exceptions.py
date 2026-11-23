"""
Unit tests for src/lib/exceptions.py
"""
import pytest
from src.lib.exceptions import (
    DataValidationError,
    CircularDataError,
    DownloadError,
    ConfigurationError
)

def test_data_validation_error():
    """Test DataValidationError instantiation."""
    with pytest.raises(DataValidationError) as exc_info:
        raise DataValidationError("Invalid data format")
    assert "Invalid data format" in str(exc_info.value)

def test_circular_data_error():
    """Test CircularDataError instantiation."""
    with pytest.raises(CircularDataError) as exc_info:
        raise CircularDataError("Target derived from features")
    assert "Target derived from features" in str(exc_info.value)

def test_download_error():
    """Test DownloadError instantiation."""
    with pytest.raises(DownloadError) as exc_info:
        raise DownloadError("Network timeout")
    assert "Network timeout" in str(exc_info.value)

def test_configuration_error():
    """Test ConfigurationError instantiation."""
    with pytest.raises(ConfigurationError) as exc_info:
        raise ConfigurationError("Missing config key")
    assert "Missing config key" in str(exc_info.value)