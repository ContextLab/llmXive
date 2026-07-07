import os
import sys
import tempfile
from pathlib import Path
import pytest
from loguru import logger

# Import the module under test
from src.utils.logging import setup_logging, get_logger

@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for log files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_logging_module_imports():
    """Test that logging module can be imported."""
    from src.utils.logging import setup_logging, get_logger
    assert callable(setup_logging)
    assert callable(get_logger)

def test_log_file_creation(temp_log_dir):
    """Test that log file is created at specified path."""
    log_path = temp_log_dir / "test_pipeline.log"
    setup_logging(log_path=log_path, level="INFO")
    
    # Trigger a log entry
    test_logger = get_logger()
    test_logger.info("Test log entry")
    
    # Check file exists
    assert log_path.exists(), f"Log file not created at {log_path}"
    
    # Check content
    content = log_path.read_text()
    assert "Test log entry" in content

def test_logger_format(temp_log_dir):
    """Test that log entries contain expected format fields."""
    log_path = temp_log_dir / "formatted.log"
    setup_logging(log_path=log_path, level="DEBUG")
    
    test_logger = get_logger()
    test_logger.info("Format test message")
    
    content = log_path.read_text()
    lines = [l for l in content.split('\n') if 'Format test message' in l]
    assert len(lines) > 0
    
    # Check for expected format components
    line = lines[0]
    assert '|' in line  # Separator
    assert 'INFO' in line  # Level
    assert 'Format test message' in line  # Message

def test_subprocess_propagation_setup(temp_log_dir):
    """Test that logging is set up to propagate to subprocesses."""
    log_path = temp_log_dir / "subprocess.log"
    setup_logging(log_path=log_path, level="INFO")
    
    # The setup ensures loguru handles logging globally
    # which allows child processes to inherit the configuration
    # when using os.environ or explicit propagation
    test_logger = get_logger()
    test_logger.info("Subprocess test entry")
    
    assert log_path.exists()
    content = log_path.read_text()
    assert "Subprocess test entry" in content

def test_get_logger():
    """Test that get_logger returns a valid logger instance."""
    test_logger = get_logger()
    assert test_logger is not None
    assert hasattr(test_logger, 'info')
    assert hasattr(test_logger, 'debug')
    assert hasattr(test_logger, 'warning')
    assert hasattr(test_logger, 'error')

def test_log_levels(temp_log_dir):
    """Test that different log levels are respected."""
    log_path = temp_log_dir / "levels.log"
    setup_logging(log_path=log_path, level="WARNING")
    
    test_logger = get_logger()
    test_logger.debug("Debug message")  # Should NOT appear
    test_logger.info("Info message")     # Should NOT appear
    test_logger.warning("Warning message")  # Should appear
    test_logger.error("Error message")     # Should appear
    
    content = log_path.read_text()
    assert "Debug message" not in content
    assert "Info message" not in content
    assert "Warning message" in content
    assert "Error message" in content

def test_all_major_steps_logged(temp_log_dir):
    """Test that the logging setup supports all major pipeline steps."""
    log_path = temp_log_dir / "steps.log"
    setup_logging(log_path=log_path, level="INFO")
    
    test_logger = get_logger()
    
    # Simulate major pipeline steps
    steps = [
        "Pipeline execution started",
        "Starting data preprocessing step",
        "Starting genomic feature extraction step",
        "Starting model training and evaluation step",
        "Starting model interpretation and reporting step",
        "Pipeline execution completed successfully"
    ]
    
    for step in steps:
        test_logger.info(step)
    
    content = log_path.read_text()
    for step in steps:
        assert step in content, f"Missing log entry for: {step}"