import os
import sys
import json
import yaml
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from logging_config import (
    get_logger, 
    log_structured_event, 
    flush_yaml_logs, 
    save_analysis_results,
    YAMLLogHandler
)
from config import get_project_root

def test_get_logger_creates_handlers():
    """Test that get_logger creates the expected handlers."""
    logger = get_logger("test_logger")
    
    # Should have console, file, and yaml handlers
    assert len(logger.handlers) == 3, f"Expected 3 handlers, got {len(logger.handlers)}"
    
    handler_types = [type(h).__name__ for h in logger.handlers]
    assert "StreamHandler" in handler_types
    assert "FileHandler" in handler_types
    assert "YAMLLogHandler" in handler_types

def test_log_structured_event():
    """Test that structured events are logged correctly."""
    logger = get_logger("test_structured")
    
    with patch.object(YAMLLogHandler, 'emit') as mock_emit:
        log_structured_event(
            logger, 
            "TEST_EVENT", 
            "Test message", 
            {"key": "value", "number": 123}
        )
        
        # Verify emit was called
        assert mock_emit.called
        call_args = mock_emit.call_args[0][0]
        
        # Check if extra data is in the record
        assert hasattr(call_args, 'extra_data')
        assert call_args.extra_data["event_type"] == "TEST_EVENT"
        assert call_args.extra_data["key"] == "value"
        assert call_args.extra_data["number"] == 123

def test_save_analysis_results():
    """Test saving analysis results to JSON."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_path = Path(tmp_dir) / "test_results.json"
        
        results = {
            "correlation": 0.85,
            "p_value": 0.001,
            "method": "spearman",
            "note": "This is a test"
        }
        
        saved_path = save_analysis_results(results, test_path)
        
        assert saved_path.exists()
        
        with open(saved_path, 'r') as f:
            loaded_results = json.load(f)
        
        assert loaded_results == results

def test_yaml_handler_flush():
    """Test that YAML handler writes to file."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yaml_path = Path(tmp_dir) / "test.yaml"
        handler = YAMLLogHandler(yaml_path)
        
        # Create a fake log record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.extra_data = {"test_key": "test_val"}
        
        handler.emit(record)
        handler.flush_to_file()
        
        assert yaml_path.exists()
        
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["message"] == "Test message"
        assert data[0]["test_key"] == "test_val"

import logging
def test_flush_yaml_logs():
    """Test the global flush function."""
    logger = get_logger("test_flush")
    log_structured_event(logger, "FLUSH_TEST", "Flush me")
    
    # The flush function iterates root logger handlers
    flush_yaml_logs()
    
    # Verify the preprocess.yaml exists in artifacts
    project_root = get_project_root()
    yaml_file = project_root / "artifacts" / "preprocess.yaml"
    assert yaml_file.exists()
    
    with open(yaml_file, 'r') as f:
        data = yaml.safe_load(f)
    
    # Should contain at least our test record
    assert len(data) > 0
    messages = [d.get("message") for d in data]
    assert "Flush me" in messages