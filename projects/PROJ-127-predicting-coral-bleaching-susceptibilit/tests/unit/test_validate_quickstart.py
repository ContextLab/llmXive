"""
Tests for T038: validate_quickstart.py
"""
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# We need to mock the config to point to a temp directory for testing
@pytest.fixture
def temp_dirs():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        processed = root / "data" / "processed"
        processed.mkdir(parents=True)
        yield root, processed

def test_runtime_within_threshold(temp_dirs):
    """Test that a runtime under 6 hours logs success."""
    root, processed = temp_dirs
    
    # Create a mock metrics file
    metrics_file = processed / "pipeline_metrics.json"
    metrics_file.write_text(json.dumps({"runtime_seconds": 1000}))
    
    # Mock config to use our temp dirs
    with patch('validate_quickstart.PROJECT_ROOT', root):
        with patch('validate_quickstart.DATA_PROCESSED_PATH', processed):
            from validate_quickstart import main, LOG_PATH, RUNTIME_THRESHOLD_SECONDS
            
            # Run main
            main()
            
            # Check log file
            assert LOG_PATH.exists()
            content = LOG_PATH.read_text()
            assert "SUCCESS" in content
            assert "within threshold" in content
            assert "ALERT" not in content
            assert not (root / "performance_report.md").exists()

def test_runtime_exceeds_threshold(temp_dirs):
    """Test that a runtime over 6 hours generates a report."""
    root, processed = temp_dirs
    
    # Create a mock metrics file with high runtime
    metrics_file = processed / "pipeline_metrics.json"
    metrics_file.write_text(json.dumps({"runtime_seconds": 30000})) # > 21600
    
    with patch('validate_quickstart.PROJECT_ROOT', root):
        with patch('validate_quickstart.DATA_PROCESSED_PATH', processed):
            from validate_quickstart import main, LOG_PATH, REPORT_PATH
            
            main()
            
            # Check log
            assert LOG_PATH.exists()
            content = LOG_PATH.read_text()
            assert "ALERT" in content
            
            # Check report
            assert REPORT_PATH.exists()
            report_content = REPORT_PATH.read_text()
            assert "Performance Report" in report_content
            assert "Exceeded By" in report_content

def test_runtime_not_found(temp_dirs):
    """Test behavior when no metrics file is found."""
    root, processed = temp_dirs
    
    # No metrics file created
    
    with patch('validate_quickstart.PROJECT_ROOT', root):
        with patch('validate_quickstart.DATA_PROCESSED_PATH', processed):
            from validate_quickstart import main, LOG_PATH
            
            main()
            
            assert LOG_PATH.exists()
            content = LOG_PATH.read_text()
            assert "UNKNOWN" in content
            assert "artifact not found" in content
            assert not (root / "performance_report.md").exists()