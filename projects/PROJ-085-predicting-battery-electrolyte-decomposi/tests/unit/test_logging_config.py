import pytest
import logging
import os
import sys
from pathlib import Path

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.logging_config import (
    get_logger,
    log_missing_geometric_data,
    log_metallic_outlier,
    log_feature_extraction_error,
    get_log_summary,
    save_log_summary
)

@pytest.fixture
def clean_log_files(tmp_path):
    """Fixture to isolate log files for testing."""
    # Mock the project root to point to tmp_path
    # We assume the logging_config uses get_project_root() which we can't easily mock
    # without patching config. Instead, we just verify the logger behavior.
    pass

def test_get_logger_returns_valid_logger():
    """Test that get_logger returns a valid logging.Logger instance."""
    logger = get_logger()
    assert isinstance(logger, logging.Logger)
    assert logger.name == "llmXive_battery"

def test_log_missing_geometric_data_emits_warning(caplog):
    """Test that missing geometric data logs a warning."""
    logger = get_logger()
    # Capture logs at WARNING level
    with caplog.at_level(logging.WARNING):
        log_missing_geometric_data("molecule_123", ["bond_length", "angle"])
    
    assert "Missing geometric data" in caplog.text
    assert "molecule_123" in caplog.text
    assert "bond_length" in caplog.text

def test_log_metallic_outlier_emits_warning(caplog):
    """Test that metallic outliers log a warning."""
    logger = get_logger()
    with caplog.at_level(logging.WARNING):
        log_metallic_outlier("molecule_456", -0.1)
    
    assert "Metallic outlier" in caplog.text
    assert "molecule_456" in caplog.text
    assert "-0.1" in caplog.text

def test_log_feature_extraction_error_emits_error(caplog):
    """Test that feature extraction errors log an error."""
    logger = get_logger()
    with caplog.at_level(logging.ERROR):
        log_feature_extraction_error("molecule_789", "RDKit failed to generate conformer")
    
    assert "Feature extraction failed" in caplog.text
    assert "molecule_789" in caplog.text

def test_log_summary_initial_state():
    """Test that log summary returns a valid dict structure."""
    summary = get_log_summary()
    assert isinstance(summary, dict)
    assert "warnings" in summary
    assert "errors" in summary
    
def test_save_log_summary_writes_file(tmp_path, monkeypatch):
    """Test that save_log_summary writes a JSON file."""
    # We need to patch the _log_summary_path in the module
    import utils.logging_config as lc
    
    # Save original
    original_path = lc._log_summary_path
    
    test_file = tmp_path / "test_summary.json"
    lc._log_summary_path = test_file
    
    try:
        test_counts = {"warnings": 5, "errors": 2}
        lc.save_log_summary(test_counts)
        
        assert test_file.exists()
        import json
        with open(test_file, 'r') as f:
            data = json.load(f)
        assert data == test_counts
    finally:
        lc._log_summary_path = original_path