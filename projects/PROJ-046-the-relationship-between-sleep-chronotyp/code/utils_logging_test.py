"""
Tests for the logging infrastructure.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent / 'code'
sys.path.insert(0, str(code_dir))

from utils_logging import (
    get_project_root,
    ensure_log_directory,
    setup_logger,
    get_pipeline_logger,
    log_info,
    log_warning,
    log_error,
    log_abort,
    log_exclusion,
    log_exclusion_count,
    check_log_file_exists,
    read_log_file
)

@pytest.fixture
def temp_project_dir():
    """Create a temporary directory to simulate project root."""
    temp_dir = tempfile.mkdtemp()
    # Create logs directory
    os.makedirs(os.path.join(temp_dir, 'logs'))
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    yield temp_dir
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)

def test_ensure_log_directory_creates_dir(temp_project_dir):
    """Test that ensure_log_directory creates the logs folder."""
    log_dir = ensure_log_directory()
    assert log_dir.exists()
    assert log_dir.is_dir()

def test_setup_logger_creates_handlers(temp_project_dir):
    """Test that setup_logger creates console and file handlers."""
    logger = setup_logger("test_logger", "test.log")
    assert len(logger.handlers) >= 1  # At least console handler
    assert logger.level == logging.DEBUG

def test_log_info_writes_to_console(temp_project_dir, capsys):
    """Test that log_info outputs to console."""
    log_info("test", "Info message")
    captured = capsys.readouterr()
    assert "Info message" in captured.out

def test_log_warning_writes_to_file(temp_project_dir):
    """Test that log_warning writes to file."""
    log_warning("test", "Warning message")
    assert check_log_file_exists("test")
    
    content = read_log_file("test")
    assert "Warning message" in content

def test_log_abort_raises_exception(temp_project_dir):
    """Test that log_abort raises RuntimeError after logging."""
    with pytest.raises(RuntimeError) as exc_info:
        log_abort("test", "Critical failure")
    
    assert "Critical failure" in str(exc_info.value)
    assert check_log_file_exists("test")
    assert (Path(temp_project_dir) / 'logs' / 'pipeline_aborts.log').exists()

def test_log_exclusion_formats_message(temp_project_dir):
    """Test that log_exclusion formats message correctly."""
    log_exclusion("classify", "Missing acute_sleepiness", row_id="123")
    
    content = read_log_file("classify")
    assert "EXCLUDED: Missing acute_sleepiness" in content
    assert "row_id=123" in content

def test_log_exclusion_count_formats_summary(temp_project_dir):
    """Test that log_exclusion_count formats summary correctly."""
    log_exclusion_count("ingest", 5, 100)
    
    content = read_log_file("ingest")
    assert "Exclusion summary" in content
    assert "5/100" in content
    assert "5.00%" in content

def test_get_pipeline_logger_returns_same_instance(temp_project_dir):
    """Test that get_pipeline_logger returns cached instance."""
    logger1 = get_pipeline_logger("analysis")
    logger2 = get_pipeline_logger("analysis")
    assert logger1 is logger2

def test_read_log_file_raises_when_missing(temp_project_dir):
    """Test that read_log_file raises FileNotFoundError when log missing."""
    with pytest.raises(FileNotFoundError):
        read_log_file("nonexistent")

def test_check_log_file_exists_returns_false_when_missing(temp_project_dir):
    """Test check_log_file_exists returns False for missing file."""
    assert not check_log_file_exists("nonexistent")

def test_log_levels_separate_messages(temp_project_dir):
    """Test that different log levels are recorded separately."""
    log_info("levels", "Info msg")
    log_warning("levels", "Warning msg")
    log_error("levels", "Error msg")
    
    content = read_log_file("levels")
    assert "INFO" in content
    assert "WARNING" in content
    assert "ERROR" in content
