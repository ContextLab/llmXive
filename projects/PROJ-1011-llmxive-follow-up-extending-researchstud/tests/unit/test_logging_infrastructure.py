import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from utils.logging_config import (
    ensure_log_dir,
    get_logger,
    get_model_fallback_logger,
    log_model_switch,
    log_memory_error,
    log_fallback_success,
    log_fallback_failure,
    initialize_pipeline_logging
)
from utils.config import select_model_on_memory_error
import logging
import sys

def test_ensure_log_dir_creates_directory():
    """Test that ensure_log_dir creates the log directory if it doesn't exist."""
    from utils.logging_config import LOG_DIR
    # Clean up first
    if LOG_DIR.exists():
        import shutil
        shutil.rmtree(LOG_DIR)
    
    result = ensure_log_dir()
    assert result.exists()
    assert result.is_dir()

def test_get_logger_returns_valid_logger():
    """Test that get_logger returns a valid logger instance."""
    logger = get_logger("test_logger")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_logger"

def test_get_model_fallback_logger():
    """Test that get_model_fallback_logger returns a logger with correct level."""
    logger = get_model_fallback_logger()
    assert isinstance(logger, logging.Logger)
    assert logger.name == "model_fallback"
    assert logger.level == logging.INFO

@patch('utils.logging_config.logging.Logger.info')
def test_log_model_switch(mock_info):
    """Test that log_model_switch logs the correct event."""
    log_model_switch("all-MiniLM-L6-v2", "all-distilroberta-v1", "Memory constraint")
    assert mock_info.called
    call_args = mock_info.call_args[0][0]
    event = json.loads(call_args)
    assert event["event_type"] == "model_switch"
    assert event["original_model"] == "all-MiniLM-L6-v2"
    assert event["fallback_model"] == "all-distilroberta-v1"
    assert event["reason"] == "Memory constraint"

@patch('utils.logging_config.logging.Logger.warning')
def test_log_memory_error(mock_warning):
    """Test that log_memory_error logs the correct event."""
    log_memory_error("all-MiniLM-L6-v2", 4.0, 8.0)
    assert mock_warning.called
    call_args = mock_warning.call_args[0][0]
    event = json.loads(call_args)
    assert event["event_type"] == "memory_error"
    assert event["model"] == "all-MiniLM-L6-v2"
    assert event["available_memory_gb"] == 4.0
    assert event["required_memory_gb"] == 8.0

@patch('utils.logging_config.logging.Logger.info')
def test_log_fallback_success(mock_info):
    """Test that log_fallback_success logs the correct event."""
    log_fallback_success("all-MiniLM-L6-v2", "all-distilroberta-v1")
    assert mock_info.called
    call_args = mock_info.call_args[0][0]
    event = json.loads(call_args)
    assert event["event_type"] == "fallback_success"
    assert event["original_model"] == "all-MiniLM-L6-v2"
    assert event["fallback_model"] == "all-distilroberta-v1"

@patch('utils.logging_config.logging.Logger.error')
def test_log_fallback_failure(mock_error):
    """Test that log_fallback_failure logs the correct event."""
    log_fallback_failure("all-MiniLM-L6-v2", "No suitable fallback found")
    assert mock_error.called
    call_args = mock_error.call_args[0][0]
    event = json.loads(call_args)
    assert event["event_type"] == "fallback_failure"
    assert event["original_model"] == "all-MiniLM-L6-v2"
    assert event["error"] == "No suitable fallback found"

def test_select_model_on_memory_error_fallback():
    """Test that select_model_on_memory_error correctly selects a fallback model."""
    with patch('utils.config.log_memory_error') as mock_mem_error, \
         patch('utils.config.log_model_switch') as mock_switch, \
         patch('utils.config.log_fallback_success') as mock_success:
        
        model, success = select_model_on_memory_error("all-MiniLM-L6-v2", 8.0, 4.0)
        
        assert success is True
        assert model == "all-distilroberta-v1"
        mock_mem_error.assert_called_once()
        mock_switch.assert_called_once()
        mock_success.assert_called_once()

def test_select_model_on_memory_error_raises_on_failure():
    """Test that select_model_on_memory_error raises MemoryError when no fallback is available."""
    with patch('utils.config.log_memory_error'), \
         patch('utils.config.log_fallback_failure') as mock_fail:
        
        with pytest.raises(MemoryError) as exc_info:
            select_model_on_memory_error("all-MiniLM-L6-v2", 10.0, 2.0)
        
        assert "No suitable fallback model found" in str(exc_info.value)
        mock_fail.assert_called_once()

def test_initialize_pipeline_logging():
    """Test that initialize_pipeline_logging sets up logging correctly."""
    from utils.logging_config import LOG_DIR
    import shutil
    
    # Clean up first
    if LOG_DIR.exists():
        shutil.rmtree(LOG_DIR)
    
    initialize_pipeline_logging()
    assert LOG_DIR.exists()
    assert (LOG_DIR / "pipeline.log").exists()