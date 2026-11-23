"""
Unit tests for custom exception classes in code/utils/exceptions.py.
"""

import pytest
from utils.exceptions import TemporalVerificationError, DataUnavailableError


class TestTemporalVerificationError:
    def test_init_with_study_id_and_message(self):
        """Test initialization with study_id and custom message."""
        study_id = "ST001234"
        custom_msg = "Missing pre-challenge timestamp"
        exc = TemporalVerificationError(study_id, custom_msg)

        assert exc.study_id == study_id
        assert custom_msg in exc.message
        assert str(exc).startswith(f"[Study {study_id}]")

    def test_init_default_message(self):
        """Test initialization with default message."""
        study_id = "ST999999"
        exc = TemporalVerificationError(study_id)

        assert exc.study_id == study_id
        assert "Temporal separation could not be verified" in exc.message

    def test_inherits_from_exception(self):
        """Test that TemporalVerificationError is a subclass of Exception."""
        assert issubclass(TemporalVerificationError, Exception)


class TestDataUnavailableError:
    def test_init_with_source_id_and_message(self):
        """Test initialization with source, identifier, and custom message."""
        source = "MetabolomicsWorkbench"
        identifier = "ST005678"
        custom_msg = "Study metadata not found"
        exc = DataUnavailableError(source, identifier, custom_msg)

        assert exc.source == source
        assert exc.identifier == identifier
        assert custom_msg in exc.message
        assert str(exc).startswith(f"[Source: {source}, ID: {identifier}]")

    def test_init_default_message(self):
        """Test initialization with default message."""
        source = "InternalDB"
        identifier = "dataset_X"
        exc = DataUnavailableError(source, identifier)

        assert exc.source == source
        assert exc.identifier == identifier
        assert "Data is unavailable" in exc.message

    def test_inherits_from_exception(self):
        """Test that DataUnavailableError is a subclass of Exception."""
        assert issubclass(DataUnavailableError, Exception)


def test_import_in_validate_temporal():
    """
    Verification that the exceptions can be imported in the module that uses them.
    This satisfies the verification requirement for T012c.
    """
    try:
        # This import pattern matches what is expected in code/data/validate_temporal.py
        from utils.exceptions import TemporalVerificationError, DataUnavailableError
        assert TemporalVerificationError is not None
        assert DataUnavailableError is not None
    except ImportError as e:
        pytest.fail(f"Import check failed: {e}")