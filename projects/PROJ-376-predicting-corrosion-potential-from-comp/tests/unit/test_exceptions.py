import pytest
from code.utils.exceptions import DataInsufficientError, SchemaMismatchError

def test_data_insufficient_error_is_exception():
    assert issubclass(DataInsufficientError, Exception)

def test_schema_mismatch_error_is_exception():
    assert issubclass(SchemaMismatchError, Exception)