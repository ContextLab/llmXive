"""
Tests for logging and error handling infrastructure.
"""
import pytest
import logging
import os
import json
from pathlib import Path
from datetime import datetime
import sys
import io

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.logging_config import (
    setup_logging,
    get_logger,
    log_error,
    handle_pipeline_exception,
    log_pipeline_start,
    log_pipeline_complete,
    log_pipeline_failure,
    PipelineError,
    DataIngestionError,
    DescriptorCalculationError,
    AnalysisError,
    VisualizationError,
    ConfigurationError,
    LOGS_DIR
)


class TestLoggingConfiguration:
    """Tests for logging configuration."""
    
    def test_setup_logging_creates_logger(self):
        """Test that setup_logging returns a logger."""
        logger = setup_logging(log_level="DEBUG")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "molecular_pipeline"
    
    def test_setup_logging_creates_file_handler(self):
        """Test that setup_logging creates a file handler."""
        logger = setup_logging(log_level="INFO")
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) > 0
    
    def test_setup_logging_creates_console_handler(self):
        """Test that setup_logging creates a console handler."""
        logger = setup_logging(log_level="INFO", console_output=True)
        console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(console_handlers) > 0
    
    def test_get_logger_returns_same_instance(self):
        """Test that get_logger returns the same instance."""
        setup_logging(log_level="INFO")
        logger1 = get_logger()
        logger2 = get_logger()
        assert logger1 is logger2


class TestPipelineErrors:
    """Tests for custom pipeline exceptions."""
    
    def test_pipeline_error_basic(self):
        """Test basic PipelineError creation."""
        error = PipelineError("Test error", stage="test_stage")
        assert str(error) == "Test error"
        assert error.stage == "test_stage"
        assert error.details == {}
    
    def test_pipeline_error_with_details(self):
        """Test PipelineError with details."""
        error = PipelineError("Test error", stage="test_stage", details={"key": "value"})
        assert error.stage == "test_stage"
        assert error.details == {"key": "value"}
    
    def test_data_ingestion_error(self):
        """Test DataIngestionError inherits from PipelineError."""
        error = DataIngestionError("Data error", stage="ingestion")
        assert isinstance(error, PipelineError)
    
    def test_descriptor_calculation_error(self):
        """Test DescriptorCalculationError inherits from PipelineError."""
        error = DescriptorCalculationError("Desc error", stage="descriptors")
        assert isinstance(error, PipelineError)
    
    def test_analysis_error(self):
        """Test AnalysisError inherits from PipelineError."""
        error = AnalysisError("Analysis error", stage="analysis")
        assert isinstance(error, PipelineError)
    
    def test_visualization_error(self):
        """Test VisualizationError inherits from PipelineError."""
        error = VisualizationError("Viz error", stage="visualization")
        assert isinstance(error, PipelineError)
    
    def test_configuration_error(self):
        """Test ConfigurationError inherits from PipelineError."""
        error = ConfigurationError("Config error", stage="config")
        assert isinstance(error, PipelineError)


class TestLogError:
    """Tests for log_error function."""
    
    def test_log_error_returns_info_dict(self):
        """Test that log_error returns a dictionary with error info."""
        logger = setup_logging(log_level="DEBUG", console_output=False)
        test_error = ValueError("Test value error")
        
        error_info = log_error(logger, test_error, stage="test_stage")
        
        assert isinstance(error_info, dict)
        assert "timestamp" in error_info
        assert error_info["stage"] == "test_stage"
        assert error_info["error_type"] == "ValueError"
        assert "Test value error" in error_info["message"]
        assert "traceback" in error_info
    
    def test_log_error_with_details(self):
        """Test log_error with additional details."""
        logger = setup_logging(log_level="DEBUG", console_output=False)
        test_error = RuntimeError("Test runtime error")
        
        error_info = log_error(
            logger,
            test_error,
            stage="test_stage",
            details={"code": 42, "item": "test"}
        )
        
        assert error_info["details"] == {"code": 42, "item": "test"}


class TestExceptionHandler:
    """Tests for handle_pipeline_exception context manager."""
    
    def test_exception_handler_catches_exception(self):
        """Test that exception handler catches and logs exceptions."""
        logger = setup_logging(log_level="DEBUG", console_output=False)
        
        with handle_pipeline_exception(logger=logger, stage="test_stage", exit_on_error=False):
            raise ValueError("Test exception")
        
        # Should not raise
    
    def test_exception_handler_writes_to_error_log(self):
        """Test that exception handler writes to errors.log."""
        logger = setup_logging(log_level="DEBUG", console_output=False)
        
        with handle_pipeline_exception(logger=logger, stage="test_stage", exit_on_error=False):
            raise KeyError("Test key error")
        
        # Check if errors.log was created
        error_log_path = LOGS_DIR / "errors.log"
        assert error_log_path.exists()


class TestPipelineStage:
    """Tests for PipelineStage context manager."""
    
    def test_pipeline_stage_logs_start_and_complete(self):
        """Test that PipelineStage logs start and completion."""
        logger = setup_logging(log_level="DEBUG", console_output=False)
        
        from code.logging_config import PipelineStage
        
        with PipelineStage("test_stage", logger=logger):
            pass  # Do nothing
        
        # Should not raise


class TestLoggingIntegration:
    """Integration tests for logging functionality."""
    
    def test_log_pipeline_lifecycle(self):
        """Test complete pipeline logging lifecycle."""
        logger = setup_logging(log_level="INFO", console_output=False)
        
        log_pipeline_start("integration_test", logger=logger)
        log_pipeline_complete("integration_test", duration_seconds=1.5, logger=logger)
        
        # Should not raise
    
    def test_log_pipeline_failure(self):
        """Test logging pipeline failure."""
        logger = setup_logging(log_level="ERROR", console_output=False)
        
        test_error = RuntimeError("Integration test failure")
        log_pipeline_failure("integration_test", test_error, logger=logger)
        
        # Should not raise