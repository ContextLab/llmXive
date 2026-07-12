"""
Unit tests for src/utils/logging.py
"""
import pytest
import logging
from pathlib import Path
import tempfile
import os

# Import the module under test
from src.utils.logging import (
    get_logger,
    log_vlm_call,
    log_data_generation,
    log_feature_extraction,
    log_error,
    log_metrics,
    count_vlm_calls,
    verify_zero_vlm_calls,
    LOG_DIR
)


class TestLoggerSetup:
    """Tests for logger initialization and configuration."""

    def test_get_logger_returns_logger_instance(self):
        """Test that get_logger returns a valid Logger instance."""
        logger = get_logger("test_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"

    def test_logger_has_handlers(self):
        """Test that logger has both file and console handlers."""
        logger = get_logger("test_handler_check")
        assert len(logger.handlers) == 2  # File + Console

    def test_logger_level_is_debug(self):
        """Test that logger is set to DEBUG level."""
        logger = get_logger("test_level_check")
        assert logger.level == logging.DEBUG

    def test_log_file_exists(self):
        """Test that log files are created in the correct directory."""
        logger = get_logger("test_file_exists")
        # Force a log write
        logger.debug("Test message")

        # Check that at least one log file exists
        log_files = list(LOG_DIR.glob("*.log"))
        assert len(log_files) > 0

class TestLogVlmCall:
    """Tests for VLM call logging."""

    def test_log_vlm_call_success(self, caplog):
        """Test logging a successful VLM call."""
        logger = get_logger("test_vlm_success")
        with caplog.at_level(logging.INFO):
            log_vlm_call(
                logger=logger,
                model_id="test-model",
                input_tokens=100,
                output_tokens=50,
                duration_ms=123.45,
                success=True
            )

        assert any("VLM_CALL" in record.message for record in caplog.records)
        assert any("SUCCESS" in record.message for record in caplog.records)
        assert any("model=test-model" in record.message for record in caplog.records)

    def test_log_vlm_call_failure(self, caplog):
        """Test logging a failed VLM call."""
        logger = get_logger("test_vlm_failure")
        with caplog.at_level(logging.INFO):
            log_vlm_call(
                logger=logger,
                model_id="test-model",
                input_tokens=100,
                output_tokens=0,
                duration_ms=0.0,
                success=False,
                error_message="Connection timeout"
            )

        assert any("FAILED" in record.message for record in caplog.records)
        assert any("error_message" in record.message for record in caplog.records)

    def test_log_vlm_call_zero_tokens(self, caplog):
        """Test logging VLM call with zero tokens."""
        logger = get_logger("test_vlm_zero")
        with caplog.at_level(logging.INFO):
            log_vlm_call(
                logger=logger,
                model_id="empty-model",
                input_tokens=0,
                output_tokens=0,
                duration_ms=0.0,
                success=True
            )

        assert any("in=0" in record.message for record in caplog.records)
        assert any("out=0" in record.message for record in caplog.records)

class TestDataGenerationLogging:
    """Tests for data generation logging."""

    def test_log_data_generation(self, caplog):
        """Test logging data generation events."""
        logger = get_logger("test_data_gen")
        with caplog.at_level(logging.INFO):
            log_data_generation(
                logger=logger,
                event="chunk_completed",
                frame_count=1000,
                duration_seconds=12.5,
                output_path="data/raw/test.jsonl"
            )

        assert any("DATA_GEN" in record.message for record in caplog.records)
        assert any("event=chunk_completed" in record.message for record in caplog.records)
        assert any("frames=1000" in record.message for record in caplog.records)

class TestFeatureExtractionLogging:
    """Tests for feature extraction logging."""

    def test_log_feature_extraction(self, caplog):
        """Test logging feature extraction events."""
        logger = get_logger("test_feature")
        with caplog.at_level(logging.INFO):
            log_feature_extraction(
                logger=logger,
                event="feature_extracted",
                feature_count=500,
                dimension=768,
                input_path="data/raw/test.jsonl",
                output_path="data/features/test.jsonl"
            )

        assert any("FEATURE" in record.message for record in caplog.records)
        assert any("dim=768" in record.message for record in caplog.records)

class TestErrorLogging:
    """Tests for error logging."""

    def test_log_error_with_context(self, caplog):
        """Test logging errors with context."""
        logger = get_logger("test_error")
        with caplog.at_level(logging.ERROR):
            log_error(
                logger=logger,
                error_type="ValueError",
                message="Invalid dimension",
                context={"expected": 768, "actual": 512}
            )

        assert any("ERROR" in record.message for record in caplog.records)
        assert any("ValueError" in record.message for record in caplog.records)
        assert any("expected" in record.message for record in caplog.records)

class TestMetricsLogging:
    """Tests for metrics logging."""

    def test_log_metrics_basic(self, caplog):
        """Test logging basic metrics."""
        logger = get_logger("test_metrics")
        with caplog.at_level(logging.INFO):
            log_metrics(
                logger=logger,
                metric_name="F1-score",
                value=0.85
            )

        assert any("METRIC" in record.message for record in caplog.records)
        assert any("F1-score" in record.message for record in caplog.records)

    def test_log_metrics_with_baseline(self, caplog):
        """Test logging metrics with baseline comparison."""
        logger = get_logger("test_metrics_baseline")
        with caplog.at_level(logging.INFO):
            log_metrics(
                logger=logger,
                metric_name="Accuracy",
                value=0.92,
                baseline_value=0.88,
                improvement=0.04
            )

        assert any("baseline=0.8800" in record.message for record in caplog.records)
        assert any("improvement=0.0400" in record.message for record in caplog.records)

class TestVlmCallCounting:
    """Tests for VLM call counting functionality."""

    def test_count_vlm_calls_with_temp_file(self):
        """Test counting VLM calls in a temporary log file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write("2024-01-01 12:00:00 | INFO | test | VLM_CALL | model=test | status=SUCCESS\n")
            f.write("2024-01-01 12:00:01 | INFO | test | DATA_GEN | event=chunk\n")
            f.write("2024-01-01 12:00:02 | INFO | test | VLM_CALL | model=test2 | status=FAILED\n")
            temp_path = Path(f.name)

        try:
            count = count_vlm_calls(temp_path)
            assert count == 2
        finally:
            os.unlink(temp_path)

    def test_count_vlm_calls_empty_file(self):
        """Test counting VLM calls in an empty log file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write("2024-01-01 12:00:00 | INFO | test | DATA_GEN | event=chunk\n")
            temp_path = Path(f.name)

        try:
            count = count_vlm_calls(temp_path)
            assert count == 0
        finally:
            os.unlink(temp_path)

    def test_verify_zero_vlm_calls_true(self):
        """Test verify_zero_vlm_calls returns True when no calls exist."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write("2024-01-01 12:00:00 | INFO | test | DATA_GEN | event=chunk\n")
            temp_path = Path(f.name)

        try:
            assert verify_zero_vlm_calls(temp_path) is True
        finally:
            os.unlink(temp_path)

    def test_verify_zero_vlm_calls_false(self):
        """Test verify_zero_vlm_calls returns False when calls exist."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write("2024-01-01 12:00:00 | INFO | test | VLM_CALL | model=test | status=SUCCESS\n")
            temp_path = Path(f.name)

        try:
            assert verify_zero_vlm_calls(temp_path) is False
        finally:
            os.unlink(temp_path)

    def test_count_vlm_calls_nonexistent_file(self):
        """Test counting VLM calls in a non-existent file."""
        count = count_vlm_calls(Path("/nonexistent/path/file.log"))
        assert count == 0

    def test_verify_zero_vlm_calls_nonexistent_file(self):
        """Test verify_zero_vlm_calls with non-existent file."""
        assert verify_zero_vlm_calls(Path("/nonexistent/path/file.log")) is True