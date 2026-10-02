"""
Unit tests for custom exception classes in code/utils/exceptions.py.

These tests verify that all required exceptions are defined and can be
imported and raised correctly, ensuring they are available for use in
Phase 5 (User Story 3) stability checks.
"""

import pytest
import sys
import os

# Add the project root to the path to allow imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.exceptions import (
    DataLoadError,
    DataGapError,
    InsufficientSampleError,
    CausalLanguageViolationError,
    StabilityThresholdViolationError,
    LongitudinalMismatchError
)


class TestStabilityThresholdViolationError:
    """Tests specifically for StabilityThresholdViolationError (T025a)."""

    def test_exception_exists(self):
        """Verify StabilityThresholdViolationError is defined."""
        assert StabilityThresholdViolationError is not None

    def test_exception_inherits_from_exception(self):
        """Verify StabilityThresholdViolationError inherits from Exception."""
        assert issubclass(StabilityThresholdViolationError, Exception)

    def test_exception_can_be_raised(self):
        """Verify StabilityThresholdViolationError can be raised and caught."""
        with pytest.raises(StabilityThresholdViolationError) as exc_info:
            raise StabilityThresholdViolationError("Coefficient variation exceeded stability threshold")
        
        assert str(exc_info.value) == "Coefficient variation exceeded stability threshold"

    def test_exception_can_be_raised_without_message(self):
        """Verify StabilityThresholdViolationError can be raised without a message."""
        with pytest.raises(StabilityThresholdViolationError):
            raise StabilityThresholdViolationError


class TestAllExceptions:
    """General tests for all custom exceptions to ensure they are importable."""

    def test_data_load_error_importable(self):
        """Verify DataLoadError is importable."""
        assert DataLoadError is not None

    def test_data_gap_error_importable(self):
        """Verify DataGapError is importable."""
        assert DataGapError is not None

    def test_insufficient_sample_error_importable(self):
        """Verify InsufficientSampleError is importable."""
        assert InsufficientSampleError is not None

    def test_causal_language_violation_error_importable(self):
        """Verify CausalLanguageViolationError is importable."""
        assert CausalLanguageViolationError is not None

    def test_longitudinal_mismatch_error_importable(self):
        """Verify LongitudinalMismatchError is importable."""
        assert LongitudinalMismatchError is not None

    def test_all_exceptions_inherit_from_exception(self):
        """Verify all exceptions inherit from Exception."""
        exceptions = [
            DataLoadError,
            DataGapError,
            InsufficientSampleError,
            CausalLanguageViolationError,
            StabilityThresholdViolationError,
            LongitudinalMismatchError
        ]
        for exc_class in exceptions:
            assert issubclass(exc_class, Exception)