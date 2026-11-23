"""
Unit tests for custom error handling infrastructure.

Tests verify that DataInsufficientError is raised correctly
and provides meaningful error messages for pipeline control flow.
"""
import pytest
from utils.errors import DataInsufficientError


class TestDataInsufficientError:
    """Tests for the DataInsufficientError exception."""

    def test_basic_instantiation(self):
        """Test that the error can be created with a simple message."""
        msg = "Dataset too small for training"
        error = DataInsufficientError(msg)
        
        assert str(error) == msg
        assert "ERR_DATA_INSUFFICIENT" in str(error)
        assert error.missing_percentage is None
        assert error.missing_fields == []

    def test_with_missing_percentage(self):
        """Test error includes percentage when provided."""
        msg = "High missing data rate detected"
        error = DataInsufficientError(msg, missing_percentage=25.5)
        
        error_str = str(error)
        assert "25.50%" in error_str
        assert error.missing_percentage == 25.5

    def test_with_missing_fields(self):
        """Test error lists missing fields when provided."""
        msg = "Critical features missing"
        fields = ["permeability", "selectivity"]
        error = DataInsufficientError(msg, missing_fields=fields)
        
        error_str = str(error)
        assert "permeability" in error_str
        assert "selectivity" in error_str
        assert error.missing_fields == fields

    def test_error_raised_on_threshold_breach(self):
        """Simulate raising the error when data is insufficient."""
        missing_pct = 25.0
        threshold = 20.0
        
        with pytest.raises(DataInsufficientError) as exc_info:
            if missing_pct > threshold:
                raise DataInsufficientError(
                    f"Missing data ({missing_pct}%) exceeds threshold ({threshold}%)"
                )
        
        assert "ERR_DATA_INSUFFICIENT" in str(exc_info.value)
        assert str(missing_pct) in str(exc_info.value)

    def test_error_inheritance(self):
        """Verify the custom error inherits from Exception."""
        error = DataInsufficientError("Test error")
        assert isinstance(error, Exception)
        assert isinstance(error, BaseException)