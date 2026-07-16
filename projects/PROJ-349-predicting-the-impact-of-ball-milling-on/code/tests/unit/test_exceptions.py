"""
Unit tests for custom exception classes defined in src/exceptions.py.

These tests verify that exceptions are instantiated correctly,
carry the expected attributes, and produce formatted messages.
"""

import pytest
from src.exceptions import (
    DataIngestionError,
    SourceConnectionError,
    SourceAuthenticationError,
    SourceNotFoundError,
    DataFormatError,
    SchemaValidationError,
    InsufficientDataError,
    GPRResourceLimitExceeded
)

class TestDataIngestionError:
    def test_base_exception_message(self):
        exc = DataIngestionError("Generic failure", "test_source")
        assert "Generic failure" in str(exc)
        assert "test_source" in str(exc)
        assert exc.message == "Generic failure"
        assert exc.source == "test_source"

class TestSourceConnectionError:
    def test_without_status_code(self):
        exc = SourceConnectionError("Network unreachable", "nist")
        assert "Network unreachable" in str(exc)
        assert exc.status_code is None
    
    def test_with_status_code(self):
        exc = SourceConnectionError("Server down", "materials_project", status_code=503)
        assert "503" in str(exc)
        assert exc.status_code == 503

class TestSourceAuthenticationError:
    def test_message_format(self):
        exc = SourceAuthenticationError("Invalid API Key", "arxiv")
        assert "Authentication failed" in str(exc)
        assert "Invalid API Key" in str(exc)
        assert exc.source == "arxiv"

class TestSourceNotFoundError:
    def test_without_resource_id(self):
        exc = SourceNotFoundError("Dataset missing", "nist")
        assert "Dataset missing" in str(exc)
        assert exc.resource_id is None
    
    def test_with_resource_id(self):
        exc = SourceNotFoundError("Dataset missing", "nist", resource_id="NIST-12345")
        assert "NIST-12345" in str(exc)
        assert exc.resource_id == "NIST-12345"

class TestDataFormatError:
    def test_basic(self):
        exc = DataFormatError("Invalid CSV", "raw_data")
        assert "Invalid CSV" in str(exc)
        assert exc.expected_format is None
    
    def test_with_formats(self):
        exc = DataFormatError(
            "Mismatched columns", 
            "merged_data", 
            expected_format="Parquet", 
            actual_format="CSV"
        )
        assert "Parquet" in str(exc)
        assert "CSV" in str(exc)
        assert exc.expected_format == "Parquet"
        assert exc.actual_format == "CSV"

class TestSchemaValidationError:
    def test_without_missing_fields(self):
        exc = SchemaValidationError("Schema invalid", "preprocessed")
        assert exc.missing_fields == []
    
    def test_with_missing_fields(self):
        exc = SchemaValidationError(
            "Schema invalid", 
            "preprocessed", 
            missing_fields=["d50", "material_type"]
        )
        assert len(exc.missing_fields) == 2
        assert "d50" in str(exc)

class TestInsufficientDataError:
    def test_message_and_counts(self):
        exc = InsufficientDataError("Not enough rows", required_count=150, actual_count=50)
        assert "150" in str(exc)
        assert "50" in str(exc)
        assert exc.required_count == 150
        assert exc.actual_count == 50

class TestGPRResourceLimitExceeded:
    def test_attributes_and_message(self):
        exc = GPRResourceLimitExceeded(runtime_seconds=2000.5, memory_gb=6.2)
        assert "2000.5" in str(exc)
        assert "6.2" in str(exc)
        assert exc.runtime_seconds == 2000.5
        assert exc.memory_gb == 6.2
        assert "Fallback" in str(exc)