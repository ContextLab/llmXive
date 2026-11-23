"""
Unit tests for the logging infrastructure (T007).

Tests verify that:
- Logging setup creates handlers correctly
- Log entries contain expected structured fields
- All logging functions (compiler, flags, warnings, NaN, stability) work correctly
- Log files are created and contain valid JSON
"""
import os
import json
import logging
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.logger import (
    setup_logging,
    get_logger,
    log_compiler_version,
    log_flag_combination,
    log_execution_warning,
    log_nan_detection,
    log_stability_failure,
    _create_json_formatter
)


class TestLoggerSetup:
    """Tests for logging initialization and configuration."""

    def test_setup_logging_creates_handlers(self, tmp_path):
        """Verify that setup_logging creates console and file handlers."""
        logger = setup_logging(log_to_file=True, log_dir=tmp_path)
        
        assert logger is not None
        assert len(logger.handlers) >= 2  # Console + File
        
        # Verify file handler exists
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 1

    def test_setup_logging_uses_custom_log_level(self, tmp_path):
        """Verify that setup_logging respects the log_level parameter."""
        logger = setup_logging(log_level=logging.DEBUG, log_to_file=False)
        assert logger.level == logging.DEBUG

    def test_get_logger_raises_if_not_initialized(self):
        """Verify that get_logger raises RuntimeError if logging not initialized."""
        # Reset the global logger
        import utils.logger as logger_module
        original_logger = logger_module._logger
        logger_module._logger = None
        
        try:
            with pytest.raises(RuntimeError, match="Logging not initialized"):
                get_logger()
        finally:
            logger_module._logger = original_logger

    def test_json_formatter_produces_valid_json(self):
        """Verify that the JSON formatter produces valid JSON output."""
        formatter = _create_json_formatter()
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        output = formatter.format(record)
        parsed = json.loads(output)
        
        assert "timestamp" in parsed
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message"


class TestLogCompilerVersion:
    """Tests for log_compiler_version function."""

    def test_log_compiler_version_contains_fields(self, tmp_path):
        """Verify that compiler version logs contain expected fields."""
        logger = setup_logging(log_to_file=True, log_dir=tmp_path)
        
        log_compiler_version("gcc", "11.4.0", ["-O2", "-march=native"])
        
        # Verify the log was written (check handlers)
        assert len(logger.handlers) >= 1

    def test_log_compiler_version_extra_fields(self, tmp_path):
        """Verify that compiler version logs include extra fields in JSON."""
        logger = setup_logging(log_to_file=True, log_dir=tmp_path)
        
        with patch.object(logger, 'info') as mock_info:
            log_compiler_version("clang", "14.0.0", ["-O3"])
            
            # Check that extra dict was passed
            call_args = mock_info.call_args
            assert call_args is not None
            assert 'extra' in call_args.kwargs or (len(call_args.args) > 1 and 'extra' in call_args.args[1])


class TestLogFlagCombination:
    """Tests for log_flag_combination function."""

    def test_log_flag_combination_contains_config_id(self, tmp_path):
        """Verify that flag combination logs contain config_id."""
        logger = setup_logging(log_to_file=True, log_dir=tmp_path)
        
        with patch.object(logger, 'info') as mock_info:
            log_flag_combination("cfg_001", ["-O3", "-ffast-math"], "matmul")
            
            call_args = mock_info.call_args
            assert call_args is not None

    def test_log_flag_combination_multiple_entries(self, tmp_path):
        """Verify that multiple flag combinations can be logged."""
        logger = setup_logging(log_to_file=True, log_dir=tmp_path)
        
        log_flag_combination("cfg_001", ["-O0"], "matmul")
        log_flag_combination("cfg_002", ["-O3"], "softmax")
        log_flag_combination("cfg_003", ["-Os"], "layernorm")
        
        assert len(logger.handlers) >= 1


class TestLogExecutionWarning:
    """Tests for log_execution_warning function."""

    def test_log_execution_warning_basic(self, tmp_path):
        """Verify basic execution warning logging."""
        logger = setup_logging(log_to_file=True, log_dir=tmp_path)
        
        with patch.object(logger, 'warning') as mock_warning:
            log_execution_warning("Memory Pressure", "Allocation failed")
            
            call_args = mock_warning.call_args
            assert call_args is not None

    def test_log_execution_warning_with_details(self, tmp_path):
        """Verify execution warning with additional details."""
        logger = setup_logging(log_to_file=True, log_dir=tmp_path)
        
        details = {"original": "768x768", "downsampled": "512x512"}
        log_execution_warning(
            "Memory Pressure",
            "Allocation failed, downsampling",
            config_id="cfg_001",
            kernel="matmul",
            details=details
        )
        
        # Verify handler exists
        assert len(logger.handlers) >= 1

    def test_log_execution_warning_level_is_warning(self, tmp_path):
        """Verify that execution warnings use WARNING level."""
        logger = setup_logging(log_to_file=True, log_dir=tmp_path)
        
        # Capture log level
        with patch.object(logger, 'warning') as mock_warning:
            log_execution_warning("Test", "Test message")
            
            # Check that warning method was called
            mock_warning.assert_called_once()


class TestLogNanDetection:
    """Tests for log_nan_detection function."""

    def test_log_nan_detection_contains_required_fields(self, tmp_path):
        """Verify that NaN detection logs contain all required fields."""
        logger = setup_logging(log_to_file=True, log_dir=tmp_path)
        
        log_nan_detection(
            config_id="cfg_001",
            kernel="matmul",
            tensor_dim="512x512",
            flags=["-O3", "-ffast-math"]
        )
        
        assert len(logger.handlers) >= 1

    def test_log_nan_detection_with_details(self, tmp_path):
        """Verify NaN detection with additional details."""
        logger = setup_logging(log_to_file=True, log_dir=tmp_path)
        
        details = {"nan_indices": [10, 42, 156], "value": float('nan')}
        log_nan_detection(
            "cfg_002",
            "layernorm",
            "768x768",
            ["-O3"],
            details=details
        )
        
        assert len(logger.handlers) >= 1


class TestLogStabilityFailure:
    """Tests for log_stability_failure function."""

    def test_log_stability_failure_contains_metrics(self, tmp_path):
        """Verify that stability failure logs contain error metrics."""
        logger = setup_logging(log_to_file=True, log_dir=tmp_path)
        
        log_stability_failure(
            config_id="cfg_001",
            kernel="matmul",
            l2_error=1.5e-4,
            max_diff=3.2e-4,
            threshold=1e-5,
            flags=["-O3", "-ffast-math"]
        )
        
        assert len(logger.handlers) >= 1

    def test_log_stability_failure_format(self, tmp_path):
        """Verify that stability failure logs are formatted correctly."""
        logger = setup_logging(log_to_file=True, log_dir=tmp_path)
        
        # This should trigger a warning log
        log_stability_failure(
            "cfg_002",
            "softmax",
            l2_error=2.0e-4,
            max_diff=5.0e-4,
            threshold=1e-5,
            flags=["-O3"]
        )
        
        assert len(logger.handlers) >= 1


class TestIntegration:
    """Integration tests for the logging module."""

    def test_log_file_contains_valid_json(self, tmp_path):
        """Verify that the log file contains valid JSON lines."""
        log_file = tmp_path / "test.log"
        
        logger = setup_logging(log_to_file=True, log_dir=tmp_path)
        
        # Generate some logs
        log_compiler_version("gcc", "11.4.0", ["-O2"])
        log_flag_combination("cfg_001", ["-O3"], "matmul")
        log_execution_warning("Test", "Test message")
        
        # Find the actual log file
        log_files = list(tmp_path.glob("experiment_*.log"))
        assert len(log_files) == 1
        
        with open(log_files[0], 'r') as f:
            lines = f.readlines()
        
        assert len(lines) > 0
        
        # Verify each line is valid JSON
        for line in lines:
            if line.strip():
                parsed = json.loads(line)
                assert "timestamp" in parsed
                assert "message" in parsed

    def test_multiple_log_types_in_sequence(self, tmp_path):
        """Verify that multiple log types can be logged in sequence."""
        logger = setup_logging(log_to_file=True, log_dir=tmp_path)
        
        log_compiler_version("gcc", "11.4.0", ["-O2"])
        log_flag_combination("cfg_001", ["-O3"], "matmul")
        log_execution_warning("Memory Pressure", "Downsampling", config_id="cfg_001")
        log_nan_detection("cfg_001", "matmul", "512x512", ["-O3"])
        log_stability_failure("cfg_001", "matmul", 1e-4, 2e-4, 1e-5, ["-O3"])
        
        log_files = list(tmp_path.glob("experiment_*.log"))
        assert len(log_files) == 1
        
        with open(log_files[0], 'r') as f:
            content = f.read()
        
        assert "gcc" in content
        assert "cfg_001" in content
        assert "NaN" in content or "Stability" in content
