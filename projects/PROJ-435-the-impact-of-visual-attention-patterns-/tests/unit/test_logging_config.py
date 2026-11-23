import logging
import os
import json
from pathlib import Path
import pytest
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils.logging_config import (
    setup_logging,
    get_pipeline_logger,
    get_quality_logger,
    get_exclusion_logger,
    log_data_quality_warning,
    log_exclusion,
    log_pipeline_progress,
    get_project_root
)

class TestLoggingConfig:
    """Tests for the logging configuration module."""

    @pytest.fixture(autouse=True)
    def setup_logging_before_each(self):
        """Setup logging before each test."""
        setup_logging()
        yield
        # Cleanup after test if needed

    def test_project_root_exists(self):
        """Test that project root is correctly identified."""
        root = get_project_root()
        assert root.exists()
        assert (root / 'code').exists()

    def test_setup_logging_creates_handlers(self):
        """Test that setup_logging creates the required handlers."""
        root_logger = logging.getLogger()
        # Reset handlers to ensure clean state
        root_logger.handlers.clear()
        
        setup_logging()
        
        handler_names = [h.name for h in root_logger.handlers]
        # We expect file handlers for pipeline, quality, and exclusion
        # The actual names depend on how they are created, but we check count
        assert len(root_logger.handlers) >= 3

    def test_get_pipeline_logger_returns_logger(self):
        """Test that get_pipeline_logger returns a valid logger."""
        logger = get_pipeline_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == 'pipeline'

    def test_get_quality_logger_returns_logger(self):
        """Test that get_quality_logger returns a valid logger."""
        logger = get_quality_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == 'quality'

    def test_get_exclusion_logger_returns_logger(self):
        """Test that get_exclusion_logger returns a valid logger."""
        logger = get_exclusion_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == 'exclusion'

    def test_log_data_quality_warning(self, caplog):
        """Test logging data quality warnings."""
        with caplog.at_level(logging.WARNING):
            log_data_quality_warning("Test warning", {"key": "value"})
        
        assert any("Test warning" in record.message for record in caplog.records)
        assert any("key" in record.message for record in caplog.records)

    def test_log_exclusion(self, caplog):
        """Test logging exclusion events."""
        with caplog.at_level(logging.INFO):
            log_exclusion(participant_id="P123", reason="Test exclusion", data_loss_percent=15.0)
        
        assert any("EXCLUSION" in record.message for record in caplog.records)
        assert any("P123" in record.message for record in caplog.records)

    def test_log_pipeline_progress(self, caplog):
        """Test logging pipeline progress."""
        with caplog.at_level(logging.INFO):
            log_pipeline_progress("Test Step", "STARTED", "Details here")
        
        assert any("PIPELINE" in record.message for record in caplog.records)
        assert any("Test Step" in record.message for record in caplog.records)

    def test_log_files_created(self):
        """Test that log files are created in the output directory."""
        root = get_project_root()
        output_dir = root / 'output'
        
        setup_logging()
        
        # Check for log files
        log_files = list(output_dir.glob('*.log'))
        assert len(log_files) >= 3  # pipeline, quality, exclusions

    def test_exclusion_log_format(self):
        """Test that exclusion logs contain structured JSON data."""
        root = get_project_root()
        exclusion_log_path = root / 'output' / 'exclusions.log'
        
        # Clear previous logs
        if exclusion_log_path.exists():
            exclusion_log_path.unlink()
        
        setup_logging()
        log_exclusion(participant_id="P999", reason="Quality Check Failed")
        
        assert exclusion_log_path.exists()
        with open(exclusion_log_path, 'r') as f:
            content = f.read()
            assert "P999" in content
            assert "Quality Check Failed" in content
            # Check for JSON structure
            assert "EXCLUSION:" in content