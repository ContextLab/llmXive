import os
import logging
import pytest
from pathlib import Path
import sys

# Ensure code directory is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_logging import (
    ensure_directories,
    setup_logging,
    get_data_quality_logger,
    get_model_diagnostics_logger,
    LOG_DIR,
    DATA_QUALITY_LOG,
    MODEL_DIAGNOSTICS_LOG
)

@pytest.fixture(autouse=True)
def setup_log_environment(tmp_path, monkeypatch):
    """
    Configure a temporary directory for logs during tests to avoid polluting the real project state.
    """
    # Override the global LOG_DIR to point to a temp directory
    temp_log_dir = tmp_path / "results" / "logs"
    monkeypatch.setattr("setup_logging.LOG_DIR", temp_log_dir)
    # Also update the module's LOG_DIR reference if it was imported elsewhere
    # In this test scope, we rely on the fixture to ensure the module uses the temp dir
    # by patching the attribute before import or using the patched attribute directly.
    # Since we are importing the module above, we need to ensure the module sees the new path.
    # The simplest way is to re-import or patch the module attribute.
    import setup_logging
    setup_logging.LOG_DIR = temp_log_dir
    
    return temp_log_dir

def test_ensure_directories_creates_log_folder(setup_log_environment):
    """Test that ensure_directories creates the log directory if it doesn't exist."""
    log_dir = setup_log_environment
    assert not log_dir.exists()
    
    ensure_directories()
    
    assert log_dir.exists()
    assert log_dir.is_dir()

def test_setup_logging_creates_files(setup_log_environment):
    """Test that setup_logging creates the specific log files."""
    log_dir = setup_log_environment
    
    setup_logging()
    
    data_quality_path = log_dir / DATA_QUALITY_LOG
    model_diagnostics_path = log_dir / MODEL_DIAGNOSTICS_LOG
    
    assert data_quality_path.exists(), f"Data quality log file {data_quality_path} was not created."
    assert model_diagnostics_path.exists(), f"Model diagnostics log file {model_diagnostics_path} was not created."

def test_get_data_quality_logger_returns_valid_logger(setup_log_environment):
    """Test that the data quality logger is configured and writes to file."""
    setup_logging()
    logger = get_data_quality_logger()
    
    assert isinstance(logger, logging.Logger)
    assert logger.name == "data_quality"
    assert logger.level == logging.INFO
    
    # Verify handler is attached
    assert len(logger.handlers) > 0, "Logger has no handlers attached."
    assert any(isinstance(h, logging.FileHandler) for h in logger.handlers), "No FileHandler attached to data_quality logger."

def test_get_model_diagnostics_logger_returns_valid_logger(setup_log_environment):
    """Test that the model diagnostics logger is configured and writes to file."""
    setup_logging()
    logger = get_model_diagnostics_logger()
    
    assert isinstance(logger, logging.Logger)
    assert logger.name == "model_diagnostics"
    assert logger.level == logging.INFO
    
    # Verify handler is attached
    assert len(logger.handlers) > 0, "Logger has no handlers attached."
    assert any(isinstance(h, logging.FileHandler) for h in logger.handlers), "No FileHandler attached to model_diagnostics logger."

def test_log_entries_written_to_disk(setup_log_environment):
    """Test that actual log entries are written to the files."""
    setup_logging()
    dq_logger = get_data_quality_logger()
    md_logger = get_model_diagnostics_logger()
    
    test_msg_dq = "Test data quality entry"
    test_msg_md = "Test model diagnostics entry"
    
    dq_logger.info(test_msg_dq)
    md_logger.info(test_msg_md)
    
    # Force flush
    for handler in dq_logger.handlers:
        handler.flush()
    for handler in md_logger.handlers:
        handler.flush()
    
    log_dir = setup_log_environment
    dq_path = log_dir / DATA_QUALITY_LOG
    md_path = log_dir / MODEL_DIAGNOSTICS_LOG
    
    with open(dq_path, 'r') as f:
        content_dq = f.read()
    with open(md_path, 'r') as f:
        content_md = f.read()
    
    assert test_msg_dq in content_dq, f"Message '{test_msg_dq}' not found in {dq_path}"
    assert test_msg_md in content_md, f"Message '{test_msg_md}' not found in {md_path}"