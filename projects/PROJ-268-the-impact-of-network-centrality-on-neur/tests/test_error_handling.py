import pytest
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from error_handling import (
    DataGapError, 
    StorageLimitExceededError, 
    raise_data_gap_error, 
    raise_storage_limit_error, 
    check_and_raise_storage_limit
)

class TestDataGapError:
    def test_raise_data_gap_error_default_message(self):
        """Test that raise_data_gap_error raises the correct exception with default message."""
        with pytest.raises(DataGapError) as exc_info:
            raise_data_gap_error()
        assert "Data Gap" in str(exc_info.value)

    def test_raise_data_gap_error_custom_context(self):
        """Test that raise_data_gap_error includes custom context in the message."""
        context = "Missing subject 001"
        with pytest.raises(DataGapError) as exc_info:
            raise_data_gap_error(context)
        assert context in str(exc_info.value)
        assert "Data Gap" in str(exc_info.value)

class TestStorageLimitExceededError:
    def test_raise_storage_limit_error(self):
        """Test that raise_storage_limit_error raises the correct exception."""
        with pytest.raises(StorageLimitExceededError) as exc_info:
            raise_storage_limit_error(15.0, 12.0)
        assert "Storage Limit Exceeded" in str(exc_info.value)
        assert "15.00" in str(exc_info.value)
        assert "12.00" in str(exc_info.value)

class TestCheckAndRaiseStorageLimit:
    def test_check_passes_under_limit(self):
        """Test that check_and_raise_storage_limit passes when under limit."""
        # Should not raise any exception
        check_and_raise_storage_limit(10.0, 12.0)
        assert True  # If we reach here, no exception was raised

    def test_check_fails_over_limit(self):
        """Test that check_and_raise_storage_limit raises when over limit."""
        with pytest.raises(StorageLimitExceededError):
            check_and_raise_storage_limit(13.0, 12.0)

    def test_check_exactly_at_limit(self):
        """Test that check_and_raise_storage_limit passes when exactly at limit."""
        # The condition is > limit, so exactly at limit should pass
        check_and_raise_storage_limit(12.0, 12.0)
        assert True

    def test_check_exceeds_limit_by_small_margin(self):
        """Test that check_and_raise_storage_limit raises when slightly over limit."""
        with pytest.raises(StorageLimitExceededError):
            check_and_raise_storage_limit(12.01, 12.0)