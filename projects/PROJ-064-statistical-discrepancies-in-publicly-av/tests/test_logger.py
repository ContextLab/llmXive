import pytest
import os
import json
import tempfile
from pathlib import Path
import logging
import sys
import io

# Import the module functions
from logger import (
    JSONFormatter,
    ReproducibilityContext,
    setup_logging,
    get_logger,
    log_with_context,
    verify_reproducible,
    main
)

def test_json_formatter_basic():
    """Test that JSONFormatter produces valid JSON."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None
    )
    output = formatter.format(record)
    data = json.loads(output)
    
    assert "timestamp" in data
    assert data["level"] == "INFO"
    assert data["message"] == "Test message"
    assert data["module"] == "test"

def test_json_formatter_with_repro_keys():
    """Test that JSONFormatter includes reproducibility keys when present."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test with hashes",
        args=(),
        exc_info=None
    )
    # Manually set extra attributes
    record.checksum = "abc123"
    record.artifact_hash = "def456"
    record.reproducible_flag = True

    output = formatter.format(record)
    data = json.loads(output)

    assert data["checksum"] == "abc123"
    assert data["artifact_hash"] == "def456"
    assert data["reproducible_flag"] is True

def test_reproducibility_context():
    """Test ReproducibilityContext computes hashes correctly."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello World")
        temp_path = f.name

    try:
        logger = logging.getLogger("test_logger")
        logger.handlers = [] # Clear handlers for clean test
        with ReproducibilityContext(logger, temp_path) as ctx:
            assert ctx.reproducible_flag is True
            assert ctx.artifact_hash is not None
            assert ctx.checksum == ctx.artifact_hash
            assert len(ctx.artifact_hash) == 64 # SHA256 hex length
    finally:
        os.unlink(temp_path)

def test_verify_reproducible_valid():
    """Test verify_reproducible on a valid file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Test Data")
        temp_path = f.name

    try:
        result = verify_reproducible(temp_path)
        assert result["status"] == "verified"
        assert result["reproducible_flag"] is True
        assert "checksum" in result
        assert result["checksum"] == result["artifact_hash"]
    finally:
        os.unlink(temp_path)

def test_verify_reproducible_missing():
    """Test verify_reproducible on a missing file."""
    result = verify_reproducible("/nonexistent/path/file.txt")
    assert result["status"] == "error"
    assert result["reproducible_flag"] is False

def test_log_with_context_integration():
    """Test that log_with_context correctly attaches hashes."""
    # Setup a StringIO handler to capture logs
    logger = logging.getLogger("test_integration")
    logger.handlers = []
    logger.setLevel(logging.INFO)
    
    string_io = io.StringIO()
    handler = logging.StreamHandler(string_io)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Context Test")
        temp_path = f.name

    try:
        log_with_context(logger, logging.INFO, "Context message", artifact_path=temp_path)
        
        log_output = string_io.getvalue()
        data = json.loads(log_output.strip())
        
        assert data["message"] == "Context message"
        assert data["reproducible_flag"] is True
        assert "checksum" in data
    finally:
        os.unlink(temp_path)
        logger.removeHandler(handler)

def test_main_verify_reproducible_flag(capsys):
    """Test the CLI --verify-reproducible flag."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("CLI Test")
        temp_path = f.name

    try:
        # Mock sys.argv
        original_argv = sys.argv
        sys.argv = ["logger.py", "--verify-reproducible", temp_path]
        
        try:
            main()
        except SystemExit as e:
            assert e.code == 0
        
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["status"] == "verified"
    finally:
        os.unlink(temp_path)
        sys.argv = original_argv
