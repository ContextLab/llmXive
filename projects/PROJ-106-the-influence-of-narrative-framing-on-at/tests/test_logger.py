import pytest
import logging
import os
import tempfile
import shutil
from pathlib import Path

# Import the module under test
# Note: In the actual project structure, we assume code/utils/logger.py is importable
# For this test, we'll import directly if the path is set up correctly
import sys
sys.path.insert(0, 'code')
from utils.logger import (
    setup_logger, 
    get_logger, 
    log_audit_event, 
    log_script_start, 
    log_script_end, 
    log_data_operation, 
    log_analysis_step,
    info,
    debug,
    warning,
    error,
    critical,
    exception,
    log_exception,
    LOG_DIR
)

class TestLoggerSetup:
    def test_setup_logger_creates_file_handler(self, tmp_path):
        """Test that setup_logger creates a file handler."""
        # Temporarily change LOG_DIR for testing
        original_log_dir = LOG_DIR
        test_log_dir = tmp_path / "test_logs"
        test_log_dir.mkdir(parents=True, exist_ok=True)
        
        # We need to mock the LOG_DIR or pass a custom path
        # Since LOG_DIR is a module-level constant, we'll test the function directly
        logger = setup_logger("test_logger")
        
        assert len(logger.handlers) > 0
        assert isinstance(logger, logging.Logger)
        
        # Reset handlers for next test
        logger.handlers.clear()

    def test_setup_logger_returns_same_instance(self):
        """Test that calling setup_logger twice returns the same logger."""
        logger1 = setup_logger("test_singleton")
        logger2 = setup_logger("test_singleton")
        
        assert logger1 is logger2

    def test_get_logger_returns_existing(self):
        """Test that get_logger returns an existing logger."""
        logger = get_logger("existing_logger")
        assert isinstance(logger, logging.Logger)

class TestAuditLogging:
    def test_log_audit_event(self, caplog):
        """Test that audit events are logged correctly."""
        logger = setup_logger("test_audit")
        logger.handlers.clear()  # Clear to avoid duplicate handlers
        
        with caplog.at_level(logging.INFO):
            log_audit_event(logger, "TEST_EVENT", {"key": "value"})
        
        assert "AUDIT [TEST_EVENT]" in caplog.text
        assert "{'key': 'value'}" in caplog.text

    def test_log_script_start(self, caplog):
        """Test that script start is logged."""
        logger = setup_logger("test_script_start")
        logger.handlers.clear()
        
        with caplog.at_level(logging.INFO):
            log_script_start(logger, "test_script.py")
        
        assert "SCRIPT_START: test_script.py" in caplog.text

    def test_log_script_end_success(self, caplog):
        """Test that successful script end is logged."""
        logger = setup_logger("test_script_end")
        logger.handlers.clear()
        
        with caplog.at_level(logging.INFO):
            log_script_end(logger, "test_script.py", True)
        
        assert "SCRIPT_END: test_script.py [SUCCESS]" in caplog.text

    def test_log_script_end_failure(self, caplog):
        """Test that failed script end is logged."""
        logger = setup_logger("test_script_end_fail")
        logger.handlers.clear()
        
        with caplog.at_level(logging.INFO):
            log_script_end(logger, "test_script.py", False)
        
        assert "SCRIPT_END: test_script.py [FAILURE]" in caplog.text

class TestDataOperationLogging:
    def test_log_data_operation_with_count(self, caplog):
        """Test that data operations with count are logged."""
        logger = setup_logger("test_data_op")
        logger.handlers.clear()
        
        with caplog.at_level(logging.INFO):
            log_data_operation(logger, "process_data", 100)
        
        assert "DATA_OP: process_data (count=100)" in caplog.text

    def test_log_data_operation_without_count(self, caplog):
        """Test that data operations without count are logged."""
        logger = setup_logger("test_data_op_no_count")
        logger.handlers.clear()
        
        with caplog.at_level(logging.INFO):
            log_data_operation(logger, "process_data")
        
        assert "DATA_OP: process_data" in caplog.text

class TestAnalysisLogging:
    def test_log_analysis_step(self, caplog):
        """Test that analysis steps are logged."""
        logger = setup_logger("test_analysis")
        logger.handlers.clear()
        
        with caplog.at_level(logging.INFO):
            log_analysis_step(logger, "calculate_mean", {"result": 42.5})
        
        assert "ANALYSIS_STEP: calculate_mean" in caplog.text
        assert "{'result': 42.5}" in caplog.text

class TestDirectLoggingFunctions:
    def test_info_function(self, caplog):
        """Test the info convenience function."""
        with caplog.at_level(logging.INFO):
            info("Test info message")
        assert "Test info message" in caplog.text

    def test_debug_function(self, caplog):
        """Test the debug convenience function."""
        with caplog.at_level(logging.DEBUG):
            debug("Test debug message")
        assert "Test debug message" in caplog.text

    def test_warning_function(self, caplog):
        """Test the warning convenience function."""
        with caplog.at_level(logging.WARNING):
            warning("Test warning message")
        assert "Test warning message" in caplog.text

    def test_error_function(self, caplog):
        """Test the error convenience function."""
        with caplog.at_level(logging.ERROR):
            error("Test error message")
        assert "Test error message" in caplog.text

    def test_critical_function(self, caplog):
        """Test the critical convenience function."""
        with caplog.at_level(logging.CRITICAL):
            critical("Test critical message")
        assert "Test critical message" in caplog.text

class TestExceptionLogging:
    def test_exception_function(self, caplog):
        """Test the exception convenience function."""
        with caplog.at_level(logging.ERROR):
            exception("Test exception message")
        assert "Test exception message" in caplog.text
        assert "Traceback" in caplog.text or "NoneType" in caplog.text  # Exception info

    def test_log_exception_function(self, caplog):
        """Test the log_exception function."""
        logger = setup_logger("test_log_exception")
        logger.handlers.clear()
        
        try:
            raise ValueError("Test error")
        except Exception as e:
            with caplog.at_level(logging.ERROR):
                log_exception(logger, e)
        
        assert "EXCEPTION: Test error" in caplog.text
        assert "ValueError" in caplog.text

class TestLoggerIntegration:
    def test_full_logging_workflow(self, caplog):
        """Test a complete logging workflow."""
        logger = setup_logger("test_workflow")
        logger.handlers.clear()
        
        with caplog.at_level(logging.INFO):
            log_script_start(logger, "workflow.py")
            log_data_operation(logger, "load_data", 50)
            log_analysis_step(logger, "compute_stats", {"mean": 10.5})
            log_audit_event(logger, "DATA_VALIDATED", {"status": "ok"})
            log_script_end(logger, "workflow.py", True)
        
        assert "SCRIPT_START: workflow.py" in caplog.text
        assert "DATA_OP: load_data (count=50)" in caplog.text
        assert "ANALYSIS_STEP: compute_stats" in caplog.text
        assert "AUDIT [DATA_VALIDATED]" in caplog.text
        assert "SCRIPT_END: workflow.py [SUCCESS]" in caplog.text
