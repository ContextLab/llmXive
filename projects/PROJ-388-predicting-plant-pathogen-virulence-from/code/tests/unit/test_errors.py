"""
Unit tests for the unified error handling module.
"""
import pytest
import requests
from pathlib import Path
from src.utils.errors import DataFetchError, AnalysisError, handle_data_fetch_error, handle_analysis_error


class TestDataFetchError:
    def test_data_fetch_error_basic(self):
        """Test basic DataFetchError creation."""
        error = DataFetchError("Test message")
        assert "Test message" in str(error)
        assert error.url is None
        assert error.status_code is None

    def test_data_fetch_error_with_url(self):
        """Test DataFetchError with URL and status code."""
        error = DataFetchError("Failed", url="http://example.com", status_code=404)
        assert "http://example.com" in str(error)
        assert "404" in str(error)
        assert error.url == "http://example.com"
        assert error.status_code == 404

    def test_handle_data_fetch_error_requests_exception(self):
        """Test handling of requests.exceptions."""
        response = requests.models.Response()
        response.status_code = 500
        req_err = requests.exceptions.RequestException(response=response)
        
        with pytest.raises(DataFetchError) as exc_info:
            handle_data_fetch_error(req_err, url="http://test.com", step="test")
        
        assert "500" in str(exc_info.value)
        assert "http://test.com" in str(exc_info.value)

    def test_handle_data_fetch_error_json_decode(self):
        """Test handling of JSONDecodeError."""
        json_err = ValueError("Expecting value") # Simulating JSONDecodeError
        with pytest.raises(DataFetchError) as exc_info:
            handle_data_fetch_error(json_err, step="parse")
        assert "parse" in str(exc_info.value)

    def test_handle_data_fetch_error_value_error_nan(self):
        """Test handling of ValueError with NaN."""
        val_err = ValueError("NaN value detected")
        with pytest.raises(DataFetchError) as exc_info:
            handle_data_fetch_error(val_err, step="validate")
        assert "NaN" in str(exc_info.value)


class TestAnalysisError:
    def test_analysis_error_basic(self):
        """Test basic AnalysisError creation."""
        error = AnalysisError("Test analysis error", step="pgls")
        assert "Test analysis error" in str(error)
        assert error.step == "pgls"

    def test_analysis_error_with_context(self):
        """Test AnalysisError with context."""
        error = AnalysisError("Error", step="tree", context={"key": "value"})
        assert "key" in str(error)
        assert "value" in str(error)

    def test_handle_analysis_error_generic(self):
        """Test handling of generic exception."""
        generic_err = ValueError("Something went wrong")
        with pytest.raises(AnalysisError) as exc_info:
            handle_analysis_error(generic_err, step="analysis")
        assert "Something went wrong" in str(exc_info.value)
        assert "analysis" in str(exc_info.value)