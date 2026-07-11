import pytest
import logging
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Import the module under test
from code.utils.logging import (
    get_pipeline_logger,
    get_log_file_path,
    log_pipeline_start,
    log_pipeline_end,
    log_error,
    log_metric,
    log_chunk_info
)

class TestLoggingInfrastructure:
    
    def setup_method(self):
        """Setup test fixtures."""
        # Create a temporary directory for logs during tests
        self.test_dir = tempfile.mkdtemp()
        # We temporarily override the log directory logic by patching
        # but for now, we test the logger creation and basic functionality
        # which doesn't strictly require a specific directory if we catch exceptions
        
        # Clear the cache to ensure fresh logger instances for tests
        from code.utils import logging as logging_module
        logging_module._logger_cache.clear()

    def teardown_method(self):
        """Cleanup test fixtures."""
        # Remove temporary directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        
        # Clear cache again
        from code.utils import logging as logging_module
        logging_module._logger_cache.clear()

    def test_get_pipeline_logger_returns_logger(self):
        """Test that get_pipeline_logger returns a valid Logger instance."""
        logger = get_pipeline_logger("test_logger_1")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger_1"
        assert logger.level == logging.INFO

    def test_logger_caching(self):
        """Test that calling get_pipeline_logger twice returns the same instance."""
        logger1 = get_pipeline_logger("test_logger_2")
        logger2 = get_pipeline_logger("test_logger_2")
        assert logger1 is logger2

    def test_log_pipeline_start(self, caplog):
        """Test log_pipeline_start function."""
        logger = get_pipeline_logger("test_start")
        config = {"chunk_size": 100, "method": "inertia"}
        
        with caplog.at_level(logging.INFO):
            log_pipeline_start(logger, config)
        
        assert "PIPELINE START" in caplog.text
        assert "Timestamp" in caplog.text
        assert "Configuration" in caplog.text

    def test_log_pipeline_end_success(self, caplog):
        """Test log_pipeline_end for successful run."""
        logger = get_pipeline_logger("test_end")
        
        with caplog.at_level(logging.INFO):
            log_pipeline_end(logger, success=True, duration=12.5)
        
        assert "PIPELINE COMPLETED SUCCESSFULLY" in caplog.text
        assert "12.5" in caplog.text

    def test_log_pipeline_end_failure(self, caplog):
        """Test log_pipeline_end for failed run."""
        logger = get_pipeline_logger("test_end_fail")
        
        with caplog.at_level(logging.ERROR):
            log_pipeline_end(logger, success=False)
        
        assert "PIPELINE FAILED" in caplog.text

    def test_log_error_with_exception(self, caplog):
        """Test log_error with an exception."""
        logger = get_pipeline_logger("test_error")
        try:
            raise ValueError("Test error")
        except Exception as e:
            with caplog.at_level(logging.ERROR):
                log_error(logger, "Something went wrong", exception=e)
        
        assert "Something went wrong" in caplog.text
        assert "ValueError" in caplog.text

    def test_log_metric(self, caplog):
        """Test log_metric function."""
        logger = get_pipeline_logger("test_metric")
        
        with caplog.at_level(logging.INFO):
            log_metric(logger, "accuracy", 0.95, stage="validation")
        
        assert "[validation]" in caplog.text
        assert "accuracy" in caplog.text
        assert "0.95" in caplog.text

    def test_log_chunk_info(self, caplog):
        """Test log_chunk_info function."""
        logger = get_pipeline_logger("test_chunk")
        
        with caplog.at_level(logging.INFO):
            log_chunk_info(logger, chunk_id=5, total_chunks=10, 
                           records_processed=1000, elapsed_seconds=2.5)
        
        assert "Chunk 5/10" in caplog.text
        assert "50.0" in caplog.text
        assert "1000" in caplog.text
        assert "2.5" in caplog.text

    def test_get_log_file_path(self):
        """Test get_log_file_path returns path or None."""
        logger = get_pipeline_logger("test_path")
        path = get_log_file_path(logger)
        # It might be None if file logging failed or wasn't set up in test env
        # but the function should not crash
        assert path is None or isinstance(path, str)
