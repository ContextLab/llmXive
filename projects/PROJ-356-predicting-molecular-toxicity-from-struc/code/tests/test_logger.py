"""
Tests for the logging infrastructure.
"""

import logging
import os
import tempfile
from pathlib import Path
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from src.utils.logger import (
    get_logger,
    log_data_count,
    log_error,
    log_checksum,
    log_pipeline_stage,
    setup_default_logger
)


class TestLogger:
    """Test cases for logger configuration and functionality."""
    
    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a valid Logger instance."""
        logger = get_logger("test_logger_1")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger_1"
    
    def test_get_logger_singleton(self):
        """Test that get_logger returns the same instance for the same name."""
        logger1 = get_logger("test_logger_2")
        logger2 = get_logger("test_logger_2")
        assert logger1 is logger2
    
    def test_logger_has_handlers(self):
        """Test that logger has both console and file handlers."""
        logger = get_logger("test_logger_3")
        assert len(logger.handlers) >= 2  # Console and file
    
    def test_log_data_count(self, caplog):
        """Test data count logging."""
        logger = get_logger("test_logger_4")
        with caplog.at_level(logging.INFO):
            log_data_count(logger, "test_source", 100, "loaded")
            assert "DATA_COUNT" in caplog.text
            assert "source=test_source" in caplog.text
            assert "count=100" in caplog.text
    
    def test_log_data_count_with_details(self, caplog):
        """Test data count logging with details."""
        logger = get_logger("test_logger_5")
        with caplog.at_level(logging.INFO):
            log_data_count(
                logger, 
                "test_source", 
                50, 
                "filtered", 
                details="MW < 1000"
            )
            assert "details=MW < 1000" in caplog.text
    
    def test_log_error(self, caplog):
        """Test error logging."""
        logger = get_logger("test_logger_6")
        with caplog.at_level(logging.ERROR):
            log_error(logger, "ValidationError", "Invalid SMILES")
            assert "ERROR" in caplog.text
            assert "type=ValidationError" in caplog.text
            assert "message=Invalid SMILES" in caplog.text
    
    def test_log_error_with_context(self, caplog):
        """Test error logging with context."""
        logger = get_logger("test_logger_7")
        with caplog.at_level(logging.ERROR):
            log_error(
                logger, 
                "DownloadError", 
                "Failed to fetch data",
                context={"url": "https://example.com", "retry": 3}
            )
            assert "url=https://example.com" in caplog.text
            assert "retry=3" in caplog.text
    
    def test_log_checksum(self, caplog):
        """Test checksum logging."""
        logger = get_logger("test_logger_8")
        with caplog.at_level(logging.INFO):
            log_checksum(logger, "data/test.csv", "abc123def456")
            assert "CHECKSUM" in caplog.text
            assert "file=data/test.csv" in caplog.text
            assert "hash=abc123def456" in caplog.text
    
    def test_log_checksum_with_algorithm(self, caplog):
        """Test checksum logging with custom algorithm."""
        logger = get_logger("test_logger_9")
        with caplog.at_level(logging.INFO):
            log_checksum(logger, "data/test.csv", "md5hash", algorithm="md5")
            assert "algorithm=md5" in caplog.text
    
    def test_log_pipeline_stage(self, caplog):
        """Test pipeline stage logging."""
        logger = get_logger("test_logger_10")
        with caplog.at_level(logging.INFO):
            log_pipeline_stage(logger, "download", "completed", duration_seconds=10.5)
            assert "PIPELINE" in caplog.text
            assert "stage=download" in caplog.text
            assert "status=completed" in caplog.text
            assert "duration=10.50s" in caplog.text
    
    def test_log_pipeline_stage_with_metrics(self, caplog):
        """Test pipeline stage logging with metrics."""
        logger = get_logger("test_logger_11")
        with caplog.at_level(logging.INFO):
            log_pipeline_stage(
                logger, 
                "training", 
                "completed",
                metrics={"roc_auc": 0.85, "f1": 0.82}
            )
            assert "roc_auc=0.85" in caplog.text
            assert "f1=0.82" in caplog.text
    
    def test_setup_default_logger(self):
        """Test setup_default_logger returns the default logger."""
        logger = setup_default_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "toxicity_pipeline"
