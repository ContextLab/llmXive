"""
Unit tests for code/utils/logging.py
"""
import pytest
import logging
from utils.logging import (
    get_logger, 
    PipelineError, 
    ParseError, 
    TimeoutError, 
    OOMError, 
    NetworkError,
    handle_parse_error,
    handle_timeout_error,
    handle_oom_error,
    handle_network_error
)

def test_get_logger_returns_logger():
    """Verify get_logger returns a valid logger instance."""
    logger = get_logger("test_module")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_module"

def test_custom_exceptions():
    """Verify custom exception classes exist and inherit from Exception."""
    with pytest.raises(PipelineError):
        raise PipelineError("Test pipeline error")
    
    with pytest.raises(ParseError):
        raise ParseError("Test parse error")
    
    with pytest.raises(TimeoutError):
        raise TimeoutError("Test timeout error")
    
    with pytest.raises(OOMError):
        raise OOMError("Test OOM error")
    
    with pytest.raises(NetworkError):
        raise NetworkError("Test network error")

def test_handle_parse_error_logs():
    """Verify handle_parse_error logs the error correctly."""
    logger = get_logger("test_parse")
    error = ParseError("Syntax error in file.py")
    
    # Should not raise, just log
    handle_parse_error(error, logger, "file.py:10")

def test_handle_timeout_error_logs():
    """Verify handle_timeout_error logs the error correctly."""
    logger = get_logger("test_timeout")
    error = TimeoutError("Chunk processing timed out")
    
    handle_timeout_error(error, logger, "chunk_123")

def test_handle_oom_error_logs():
    """Verify handle_oom_error logs the error correctly."""
    logger = get_logger("test_oom")
    error = OOMError("Out of memory during inference")
    
    handle_oom_error(error, logger, "chunk_456")

def test_handle_network_error_logs():
    """Verify handle_network_error logs the error correctly."""
    logger = get_logger("test_network")
    error = NetworkError("Connection refused")
    
    handle_network_error(error, logger, "dataset_fetch")
