"""
Tests for the custom exceptions and logging infrastructure defined in T007.
"""

import pytest
import logging
from code.exceptions import DataInsufficientError, PowerWarning, SHAPError
from code.logging_config import setup_logger, handle_data_insufficient, handle_power_warning, handle_shap_error


class TestDataInsufficientError:
    def test_default_initialization(self):
        """Test default values for DataInsufficientError."""
        error = DataInsufficientError("Not enough data")
        assert error.message == "Not enough data"
        assert error.sample_count == 0
        assert error.required_count == 30
        assert "Available: 0" in str(error)
        assert "Required: 30" in str(error)

    def test_custom_initialization(self):
        """Test custom values for DataInsufficientError."""
        error = DataInsufficientError("Too few samples", sample_count=10, required_count=50)
        assert error.message == "Too few samples"
        assert error.sample_count == 10
        assert error.required_count == 50
        assert "Available: 10" in str(error)
        assert "Required: 50" in str(error)

    def test_inheritance(self):
        """Test that DataInsufficientError is a subclass of Exception."""
        assert issubclass(DataInsufficientError, Exception)


class TestPowerWarning:
    def test_default_initialization(self):
        """Test default values for PowerWarning."""
        warning = PowerWarning("Low power")
        assert warning.message == "Low power"
        assert warning.sample_count == 0
        assert "Available: 0" in str(warning)
        assert "Falling back to LOOCV" in str(warning)

    def test_custom_initialization(self):
        """Test custom values for PowerWarning."""
        warning = PowerWarning("Critical low power", sample_count=5)
        assert warning.message == "Critical low power"
        assert warning.sample_count == 5
        assert "Available: 5" in str(warning)

    def test_inheritance(self):
        """Test that PowerWarning is a subclass of UserWarning."""
        assert issubclass(PowerWarning, UserWarning)


class TestSHAPError:
    def test_default_initialization(self):
        """Test default values for SHAPError."""
        error = SHAPError("SHAP calculation failed")
        assert error.message == "SHAP calculation failed"
        assert error.original_error is None
        assert "Original error" not in str(error)

    def test_with_original_error(self):
        """Test SHAPError with an underlying exception."""
        original = ValueError("Dimension mismatch")
        error = SHAPError("SHAP calculation failed", original_error=original)
        assert error.message == "SHAP calculation failed"
        assert error.original_error is original
        assert "Original error: ValueError" in str(error)
        assert "Dimension mismatch" in str(error)

    def test_inheritance(self):
        """Test that SHAPError is a subclass of Exception."""
        assert issubclass(SHAPError, Exception)


class TestLoggingHandlers:
    @pytest.fixture
    def logger(self):
        """Create a test logger."""
        return setup_logger("test_logger", level=logging.DEBUG)

    def test_handle_data_insufficient_raises(self, logger):
        """Test that handle_data_insufficient logs and re-raises."""
        error = DataInsufficientError("Test error", sample_count=5)
        with pytest.raises(DataInsufficientError):
            handle_data_insufficient(logger, error)

    def test_handle_power_warning_logs_only(self, logger):
        """Test that handle_power_warning logs but does not raise."""
        warning = PowerWarning("Test warning", sample_count=10)
        # Should not raise
        handle_power_warning(logger, warning)

    def test_handle_shap_error_raises(self, logger):
        """Test that handle_shap_error logs and re-raises."""
        original = RuntimeError("Simulated failure")
        error = SHAPError("SHAP failed", original_error=original)
        with pytest.raises(SHAPError):
            handle_shap_error(logger, error)

    def test_handle_shap_error_without_original(self, logger):
        """Test handle_shap_error without an original exception."""
        error = SHAPError("SHAP failed without original")
        with pytest.raises(SHAPError):
            handle_shap_error(logger, error)
