"""
Unit tests for data ingestion error handling.

This module validates that the error handling wrapper correctly
catches and transforms various failure modes into the project's
custom exception hierarchy.
"""
import pytest
from unittest.mock import patch, MagicMock
import requests
import json
import logging

# Import the specific exceptions defined in the project API
# Using the path provided in the API surface list
from code.src.exceptions import (
    DataIngestionError,
    SourceConnectionError,
    SourceAuthenticationError,
    SourceNotFoundError,
    DataFormatError,
    GPRResourceLimitExceeded
)

# Import the error handler to be tested
# Using the path provided in the API surface list
from code.src.utils.error_handler import handle_ingestion_errors

class MockIngestor:
    """Mock class to simulate an ingestion function that can fail."""
    
    def __init__(self, behavior="success"):
        self.behavior = behavior
    
    @handle_ingestion_errors(source="mock_source")
    def run(self):
        if self.behavior == "connection_error":
            raise requests.exceptions.ConnectionError("Network unreachable")
        elif self.behavior == "timeout":
            raise requests.exceptions.Timeout("Request timed out")
        elif self.behavior == "auth":
            # Create a mock response object for HTTPError
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.reason = "Unauthorized"
            raise requests.exceptions.HTTPError(response=mock_response)
        elif self.behavior == "not_found":
            # Create a mock response object for HTTPError
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.reason = "Not Found"
            raise requests.exceptions.HTTPError(response=mock_response)
        elif self.behavior == "bad_json":
            raise json.JSONDecodeError("Expecting value", "doc", 0)
        elif self.behavior == "value_error":
            raise ValueError("Unexpected data format")
        elif self.behavior == "gpr_limit":
            raise GPRResourceLimitExceeded(runtime_seconds=1801, memory_gb=6.0)
        elif self.behavior == "generic_exception":
            raise RuntimeError("Unexpected crash")
        
        return {"status": "success", "data": [1, 2, 3]}

class TestIngestionErrorHandling:
    """Test suite for data ingestion error handling logic."""

    def test_success_case_no_error_raised(self):
        """Verify that successful execution returns data without raising."""
        ingestor = MockIngestor(behavior="success")
        result = ingestor.run()
        assert result["status"] == "success"
        assert result["data"] == [1, 2, 3]

    def test_connection_error_converted_to_source_connection_error(self):
        """Verify ConnectionError is wrapped into SourceConnectionError."""
        ingestor = MockIngestor(behavior="connection_error")
        with pytest.raises(SourceConnectionError) as exc_info:
            ingestor.run()
        
        assert "mock_source" in str(exc_info.value)
        assert "ConnectionError" in str(exc_info.value)

    def test_timeout_converted_to_source_connection_error(self):
        """Verify Timeout is wrapped into SourceConnectionError."""
        ingestor = MockIngestor(behavior="timeout")
        with pytest.raises(SourceConnectionError) as exc_info:
            ingestor.run()
        
        assert "mock_source" in str(exc_info.value)

    def test_401_error_converted_to_auth_error(self):
        """Verify 401 HTTPError is wrapped into SourceAuthenticationError."""
        ingestor = MockIngestor(behavior="auth")
        with pytest.raises(SourceAuthenticationError) as exc_info:
            ingestor.run()
        
        assert "mock_source" in str(exc_info.value)
        assert "401" in str(exc_info.value)

    def test_404_error_converted_to_not_found_error(self):
        """Verify 404 HTTPError is wrapped into SourceNotFoundError."""
        ingestor = MockIngestor(behavior="not_found")
        with pytest.raises(SourceNotFoundError) as exc_info:
            ingestor.run()
        
        assert "mock_source" in str(exc_info.value)
        assert "404" in str(exc_info.value)

    def test_json_decode_error_converted_to_data_format_error(self):
        """Verify JSONDecodeError is wrapped into DataFormatError."""
        ingestor = MockIngestor(behavior="bad_json")
        with pytest.raises(DataFormatError) as exc_info:
            ingestor.run()
        
        assert "mock_source" in str(exc_info.value)
        assert "JSON" in str(exc_info.value)

    def test_value_error_converted_to_data_format_error(self):
        """Verify ValueError is wrapped into DataFormatError (data format issue)."""
        ingestor = MockIngestor(behavior="value_error")
        with pytest.raises(DataFormatError) as exc_info:
            ingestor.run()
        
        assert "mock_source" in str(exc_info.value)

    def test_gpr_resource_limit_exceeded_passthrough(self):
        """Verify GPRResourceLimitExceeded is NOT wrapped, but re-raised as-is."""
        ingestor = MockIngestor(behavior="gpr_limit")
        with pytest.raises(GPRResourceLimitExceeded) as exc_info:
            ingestor.run()
        
        # Should preserve original attributes
        assert exc_info.value.runtime_seconds == 1801
        assert exc_info.value.memory_gb == 6.0

    def test_generic_exception_converted_to_data_ingestion_error(self):
        """Verify unknown exceptions are wrapped into generic DataIngestionError."""
        ingestor = MockIngestor(behavior="generic_exception")
        with pytest.raises(DataIngestionError) as exc_info:
            ingestor.run()
        
        assert "mock_source" in str(exc_info.value)
        assert "RuntimeError" in str(exc_info.value)

    def test_ingest_handles_missing_api_key(self):
        """
        Specific test for T011: Verify that a 401 HTTPError (missing/invalid API key)
        raises DataIngestionError with the message 'API key invalid or missing'.
        
        Note: The existing error handler maps 401 to SourceAuthenticationError.
        This test asserts the specific behavior required by the task description.
        To satisfy the task requirement strictly, we verify that the exception
        raised contains the required message substring, even if the exception
        type is SourceAuthenticationError (which is a subclass of DataIngestionError).
        """
        ingestor = MockIngestor(behavior="auth")
        with pytest.raises(Exception) as exc_info:
            ingestor.run()
        
        # The task requires the message "API key invalid or missing"
        # The current implementation raises SourceAuthenticationError with a generic message.
        # We check if the exception is a DataIngestionError (or subclass) and contains the message.
        # If the message is not exactly as requested, we assert the failure to highlight the gap.
        # However, per task T011, we must implement the test that asserts the condition.
        # Since the error handler logic is in T048/T053 (hardening) and T012-T014,
        # and the task T011 specifically asks to assert the message "API key invalid or missing",
        # we assert that the exception message contains this string.
        # If the current handler raises "Authentication failed for mock_source", this test will fail,
        # indicating the handler needs adjustment to match the specific task requirement.
        
        # Check if it is a DataIngestionError (SourceAuthenticationError is one)
        assert isinstance(exc_info.value, DataIngestionError), f"Expected DataIngestionError, got {type(exc_info.value)}"
        
        # Assert the specific message required by T011
        error_message = str(exc_info.value)
        assert "API key invalid or missing" in error_message, \
            f"Expected 'API key invalid or missing' in error message, got: {error_message}"