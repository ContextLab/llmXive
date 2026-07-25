import os
import sys
import tempfile
import logging
from pathlib import Path
import pytest

# Add code directory to path
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from utils.logging_config import (
    setup_logging,
    get_quality_logger,
    get_exclusion_logger,
    get_pipeline_logger,
    log_data_quality_warning,
    log_exclusion,
    log_pipeline_progress,
    log_pipeline_error,
    _initialized,
    _loggers
)

@pytest.fixture
def temp_project_root():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        # Create expected directory structure
        (project_root / "state" / "logs").mkdir(parents=True)
        yield project_root

def test_setup_logging_creates_log_directory(temp_project_root):
    """Test that setup_logging creates the log directory."""
    log_dir = temp_project_root / "state" / "logs"
    assert log_dir.exists()
    
    setup_logging(temp_project_root)
    assert log_dir.exists()

def test_get_quality_logger_returns_logger(temp_project_root):
    """Test that get_quality_logger returns a valid logger."""
    setup_logging(temp_project_root)
    logger = get_quality_logger()
    
    assert isinstance(logger, logging.Logger)
    assert logger.name == "data_quality"
    assert logger.level == logging.DEBUG

def test_get_exclusion_logger_returns_logger(temp_project_root):
    """Test that get_exclusion_logger returns a valid logger."""
    setup_logging(temp_project_root)
    logger = get_exclusion_logger()
    
    assert isinstance(logger, logging.Logger)
    assert logger.name == "exclusions"
    assert logger.level == logging.DEBUG

def test_get_pipeline_logger_returns_logger(temp_project_root):
    """Test that get_pipeline_logger returns a valid logger."""
    setup_logging(temp_project_root)
    logger = get_pipeline_logger()
    
    assert isinstance(logger, logging.Logger)
    assert logger.name == "pipeline"
    assert logger.level == logging.DEBUG

def test_log_data_quality_warning(temp_project_root, caplog):
    """Test logging data quality warnings."""
    setup_logging(temp_project_root)
    
    with caplog.at_level(logging.WARNING):
        log_data_quality_warning("Test warning", participant_id="P001")
        
    assert any("Test warning" in record.message for record in caplog.records)
    assert any("participant=P001" in record.message for record in caplog.records)

def test_log_exclusion(temp_project_root, caplog):
    """Test logging exclusion events."""
    setup_logging(temp_project_root)
    
    with caplog.at_level(logging.INFO):
        log_exclusion("High data loss", participant_id="P002", count=1)
        
    assert any("Excluded participant P002" in record.message for record in caplog.records)
    assert any("High data loss" in record.message for record in caplog.records)

def test_log_pipeline_progress(temp_project_root, caplog):
    """Test logging pipeline progress."""
    setup_logging(temp_project_root)
    
    with caplog.at_level(logging.INFO):
        log_pipeline_progress("test_step", "Processing data", {"rows": 100})
        
    assert any("[test_step]" in record.message for record in caplog.records)
    assert any("Processing data" in record.message for record in caplog.records)
    assert any("rows=100" in record.message for record in caplog.records)

def test_log_pipeline_error(temp_project_root, caplog):
    """Test logging pipeline errors."""
    setup_logging(temp_project_root)
    
    with caplog.at_level(logging.ERROR):
        try:
            raise ValueError("Test error")
        except Exception as e:
            log_pipeline_error("test_step", "Something went wrong", exception=e)
        
    assert any("[test_step]" in record.message for record in caplog.records)
    assert any("Something went wrong" in record.message for record in caplog.records)

def test_loggers_cached(temp_project_root):
    """Test that loggers are cached and not recreated."""
    setup_logging(temp_project_root)
    
    logger1 = get_quality_logger()
    logger2 = get_quality_logger()
    
    assert logger1 is logger2
    assert "data_quality" in _loggers

def test_log_file_created(temp_project_root):
    """Test that log files are created in the correct location."""
    setup_logging(temp_project_root)
    
    # Trigger logger creation
    get_quality_logger()
    get_exclusion_logger()
    get_pipeline_logger()
    
    log_dir = temp_project_root / "state" / "logs"
    assert (log_dir / "data_quality.log").exists()
    assert (log_dir / "exclusions.log").exists()
    assert (log_dir / "pipeline.log").exists()
