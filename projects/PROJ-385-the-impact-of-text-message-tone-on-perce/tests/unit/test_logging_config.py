"""
Unit tests for the logging infrastructure (T008).
"""
import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path
code_dir = Path(__file__).parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from logging_config import setup_logging, get_logger, log_pipeline_step, log_exclusion
from config import get_processed_data_dir


class TestLoggingInfrastructure:
    """Tests for T008 logging setup."""

    def test_logger_initialization(self):
        """Test that setup_logging returns a configured logger."""
        logger = setup_logging()
        assert logger is not None
        assert logger.name == "llmXive_pipeline"
        assert logger.level == 20  # INFO

    def test_get_logger_returns_parent(self):
        """Test that get_logger returns the main logger or a child."""
        parent = setup_logging()
        child = get_logger("test_child")
        
        # Child should be a child of the parent
        assert child.name.startswith(parent.name)

    def test_log_pipeline_step_format(self, tmp_path, monkeypatch):
        """Test that log_pipeline_step writes correctly formatted messages."""
        # Mock the file handler to write to a temp file for easier inspection
        log_file = tmp_path / "test.log"
        
        # We can't easily mock the global setup in a unit test without side effects,
        # so we test the logic of the message construction via the logger directly
        # by patching the FileHandler creation in setup_logging if needed,
        # but for T008 verification, the integration script (verify_logging.py) is the primary check.
        # Here we verify the function calls don't crash.
        
        with patch('logging_config.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            log_pipeline_step("TestStep", "Details here")
            
            # Verify info was called with the correct format
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "Pipeline Step: TestStep" in call_args
            assert "Details here" in call_args

    def test_log_exclusion_format(self, tmp_path, monkeypatch):
        """Test that log_exclusion writes correctly formatted warning messages."""
        with patch('logging_config.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            log_exclusion("STRAIGHT_LINING", participant_id="P-123")
            
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args[0][0]
            assert "Exclusion: STRAIGHT_LINING" in call_args
            assert "Participant: P-123" in call_args

    def test_log_exclusion_no_participant(self, tmp_path, monkeypatch):
        """Test exclusion logging without participant ID."""
        with patch('logging_config.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            log_exclusion("MISSING_DATA")
            
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args[0][0]
            assert "Exclusion: MISSING_DATA" in call_args
            assert "Participant" not in call_args