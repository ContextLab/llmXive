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

# Import the specific exceptions defined in the project API
from code.src.exceptions import (
    DataIngestionError,
    SourceConnectionError,
    SourceAuthenticationError,
    SourceNotFoundError,
    DataFormatError,
    GPRResourceLimitExceeded
)

# Import the error handler to be tested
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
            raise requests.exceptions.HTTPError(response=MagicMock(status_code=401, reason="Unauthorized"))
        elif self.behavior == "not_found":
            raise requests.exceptions.HTTPError(response=MagicMock(status_code=404, reason="Not Found"))
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

if __name__ == "__main__":
    pytest.main([__file__, "-v"])