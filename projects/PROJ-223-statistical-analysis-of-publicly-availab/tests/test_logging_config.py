"""
Tests for the logging infrastructure (T006).
"""
import pytest
import logging
import os
from pathlib import Path
from io import StringIO

# Import the module under test
from code.logging_config import (
    logger,
    log_data_drop_counts,
    log_model_convergence,
    log_processing_step,
    get_log_file_path
)

class TestLoggingInfrastructure:
    
    def test_logger_initialized(self):
        """Verify the logger is initialized and has handlers."""
        assert logger is not None
        assert len(logger.handlers) > 0
        assert logger.level == logging.INFO

    def test_log_data_drop_counts(self, caplog):
        """Test logging of data drop counts."""
        with caplog.at_level(logging.WARNING):
            log_data_drop_counts(
                source="TestMerge",
                initial_count=1000,
                final_count=800,
                drop_reason="Missing IDs"
            )
        
        assert "DATA DROP [TestMerge]" in caplog.text
        assert "200 rows dropped" in caplog.text
        assert "Missing IDs" in caplog.text

    def test_log_model_convergence_success(self, caplog):
        """Test logging successful model convergence."""
        with caplog.at_level(logging.INFO):
            log_model_convergence(
                model_name="TestModel",
                converged=True,
                iterations=10
            )
        
        assert "MODEL STATUS [TestModel]: CONVERGED" in caplog.text
        assert "Iterations: 10" in caplog.text

    def test_log_model_convergence_failure(self, caplog):
        """Test logging failed model convergence (should be WARNING)."""
        with caplog.at_level(logging.WARNING):
            log_model_convergence(
                model_name="BadModel",
                converged=False,
                message="Max iterations reached"
            )
        
        assert "MODEL STATUS [BadModel]: FAILED TO CONVERGE" in caplog.text
        assert "Max iterations reached" in caplog.text

    def test_log_processing_step(self, caplog):
        """Test generic processing step logging."""
        with caplog.at_level(logging.INFO):
            log_processing_step(
                step_name="DataCleaning",
                status="COMPLETED",
                details={"rows_processed": 500, "time_ms": 120}
            )
        
        assert "STEP [DataCleaning]: COMPLETED" in caplog.text
        assert "rows_processed=500" in caplog.text

    def test_log_file_exists(self):
        """Verify that a log file was created on disk."""
        path = get_log_file_path()
        assert os.path.exists(path), f"Log file not found at {path}"
        assert os.path.getsize(path) > 0, "Log file is empty"