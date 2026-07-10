"""
Unit tests for logging and error handling infrastructure.
"""

import pytest
import os
import tempfile
import logging
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.logging_config import (
    configure_logging, 
    get_logger, 
    PipelineError, 
    DataIngestionError, 
    SafeExecutionBlock,
    get_log_file_path
)
from src.error_utils import validate_not_null, validate_data_frame_columns, safe_divide
import pandas as pd

class TestPipelineExceptions:
    def test_pipeline_error_basic(self):
        exc = PipelineError("Test error")
        assert str(exc) == "Test error"
        assert exc.context == {}

    def test_pipeline_error_with_context(self):
        ctx = {"key": "value"}
        exc = PipelineError("Test error", context=ctx)
        assert exc.context == ctx

    def test_data_ingestion_error_inheritance(self):
        exc = DataIngestionError("Data fail")
        assert isinstance(exc, PipelineError)

class TestLoggingConfig:
    def test_configure_logging_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            configure_logging(log_level="INFO", log_dir=tmpdir, console=False)
            
            # Check that a log file was created
            log_files = list(Path(tmpdir).glob("pipeline_*.log"))
            assert len(log_files) == 1
            
            # Verify we can get the path
            path = get_log_file_path()
            assert path.exists()

    def test_get_logger_returns_logger(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            configure_logging(log_level="DEBUG", log_dir=tmpdir, console=False)
            
            logger = get_logger("test.module")
            assert isinstance(logger, logging.Logger)
            assert logger.name == "test.module"

class TestSafeExecutionBlock:
    def test_success_case(self, caplog):
        with tempfile.TemporaryDirectory() as tmpdir:
            configure_logging(log_level="INFO", log_dir=tmpdir, console=False)
            
            with SafeExecutionBlock("Test Success"):
                pass
            
            # Check logs
            assert any("Starting phase: Test Success" in record.message for record in caplog.records)
            assert any("completed successfully" in record.message for record in caplog.records)

    def test_failure_case(self, caplog):
        with tempfile.TemporaryDirectory() as tmpdir:
            configure_logging(log_level="ERROR", log_dir=tmpdir, console=False)
            
            with pytest.raises(ValueError):
                with SafeExecutionBlock("Test Fail"):
                    raise ValueError("Intentional fail")
            
            assert any("failed" in record.message for record in caplog.records)

class TestErrorUtils:
    def test_validate_not_null_pass(self):
        validate_not_null("value", "field")
        validate_not_null([1], "list")

    def test_validate_not_null_fail_none(self):
        with pytest.raises(PipelineError):
            validate_not_null(None, "field")

    def test_validate_not_null_fail_empty(self):
        with pytest.raises(PipelineError):
            validate_not_null("", "field")

    def test_validate_df_columns_pass(self):
        df = pd.DataFrame({"a": [1], "b": [2]})
        validate_data_frame_columns(df, ["a", "b"])

    def test_validate_df_columns_fail(self):
        df = pd.DataFrame({"a": [1]})
        with pytest.raises(DataIngestionError):
            validate_data_frame_columns(df, ["a", "b"])

    def test_safe_divide_normal(self):
        assert safe_divide(10, 2) == 5.0

    def test_safe_divide_zero(self):
        assert safe_divide(10, 0) == 0.0
        assert safe_divide(10, 0, default=-1.0) == -1.0
