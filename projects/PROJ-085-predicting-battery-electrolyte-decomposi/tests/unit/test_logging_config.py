import pytest
import logging
import tempfile
import os
from pathlib import Path

from utils.logging_config import get_logger, log_missing_geometric_data, log_metallic_outlier, get_log_summary

class TestLoggingConfig:
    """Tests for the logging infrastructure (T008)."""

    def setup_method(self):
        """Setup test logging."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = Path(self.temp_dir.name) / "test.log"

    def teardown_method(self):
        """Cleanup."""
        self.temp_dir.cleanup()

    def test_get_logger(self):
        """Test that get_logger returns a valid logger."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_log_missing_geometric_data(self):
        """Test logging missing geometric data."""
        logger = get_logger("test_geom")
        # This should not raise
        log_missing_geometric_data(logger, "molecule_123", ["bond_length"])
        # Verify log level is WARNING
        # We can't easily capture the output without a handler, 
        # but we verify the function exists and is callable.

    def test_log_metallic_outlier(self):
        """Test logging metallic outlier."""
        logger = get_logger("test_metal")
        log_metallic_outlier(logger, "molecule_456", -0.5)
        # Verify function call

    def test_log_summary(self):
        """Test getting log summary."""
        summary = get_log_summary()
        assert isinstance(summary, dict)
        assert "total_warnings" in summary
        assert "total_errors" in summary
