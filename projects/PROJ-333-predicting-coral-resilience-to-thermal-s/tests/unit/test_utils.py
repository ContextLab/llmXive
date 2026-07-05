"""
Unit tests for code/utils.py functionality.
"""
import logging
import os
import tempfile
from pathlib import Path
import pytest
import hashlib

from code.utils import (
    setup_logger,
    validate_checksum,
    calculate_checksum,
    handle_critical_error,
    log_pipeline_start,
    log_pipeline_end
)


class TestSetupLogger:
    def test_console_logger_only(self, tmp_path):
        logger = setup_logger("test_console", console=True, log_file=None, level=logging.DEBUG)
        assert logger.name == "test_console"
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)

    def test_file_logger_only(self, tmp_path):
        log_file = tmp_path / "test.log"
        logger = setup_logger("test_file", log_file=log_file, console=False, level=logging.WARNING)
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.FileHandler)
        assert log_file.exists()

    def test_both_handlers(self, tmp_path):
        log_file = tmp_path / "test_both.log"
        logger = setup_logger("test_both", log_file=log_file, console=True, level=logging.INFO)
        assert len(logger.handlers) == 2

    def test_duplicate_call_ignores(self, tmp_path):
        log_file = tmp_path / "test_dup.log"
        logger = setup_logger("test_dup", log_file=log_file, console=True, level=logging.INFO)
        initial_count = len(logger.handlers)
        
        # Call again with different settings
        logger2 = setup_logger("test_dup", log_file=tmp_path / "other.log", console=False)
        
        # Handler count should remain the same
        assert len(logger2.handlers) == initial_count


class TestChecksum:
    def test_calculate_checksum_sha256(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Hello, world!")
            temp_path = Path(f.name)

        try:
            checksum = calculate_checksum(temp_path, "sha256")
            # Manually calculate expected
            hasher = hashlib.sha256(b"Hello, world!")
            expected = hasher.hexdigest()
            assert checksum == expected
        finally:
            os.unlink(temp_path)

    def test_validate_checksum_success(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Test data")
            temp_path = Path(f.name)

        try:
            correct_checksum = calculate_checksum(temp_path)
            assert validate_checksum(temp_path, correct_checksum) is True
        finally:
            os.unlink(temp_path)

    def test_validate_checksum_failure(self, caplog):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Test data")
            temp_path = Path(f.name)

        try:
            wrong_checksum = "0" * 64  # Invalid checksum
            with caplog.at_level(logging.WARNING):
                result = validate_checksum(temp_path, wrong_checksum)
            assert result is False
            assert "Checksum mismatch" in caplog.text
        finally:
            os.unlink(temp_path)

    def test_validate_checksum_file_not_found(self):
        fake_path = Path("/nonexistent/path/file.txt")
        with pytest.raises(FileNotFoundError):
            validate_checksum(fake_path, "dummy_checksum")

    def test_calculate_checksum_file_not_found(self):
        fake_path = Path("/nonexistent/path/file.txt")
        with pytest.raises(FileNotFoundError):
            calculate_checksum(fake_path)

    def test_unsupported_algorithm(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("data")
        
        with pytest.raises(ValueError, match="Unsupported hash algorithm"):
            calculate_checksum(test_file, algorithm="invalid_algo")

    def test_md5_algorithm(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("MD5 Test")
            temp_path = Path(f.name)

        try:
            checksum = calculate_checksum(temp_path, "md5")
            hasher = hashlib.md5(b"MD5 Test")
            expected = hasher.hexdigest()
            assert checksum == expected
        finally:
            os.unlink(temp_path)


class TestHandleCriticalError:
    def test_handle_critical_error_exits(self, monkeypatch):
        exit_code = None
        
        def mock_exit(code):
            nonlocal exit_code
            exit_code = code
            raise SystemExit(code)
        
        monkeypatch.setattr("sys.exit", mock_exit)
        
        with pytest.raises(SystemExit):
            handle_critical_error("Test fatal error", error_code=42)
        
        assert exit_code == 42


class TestLoggingHelpers:
    def test_log_pipeline_start(self, caplog):
        caplog.set_level(logging.INFO)
        log_pipeline_start("T005", config={"key": "value"})
        assert "Starting task: T005" in caplog.text

    def test_log_pipeline_end_success(self, caplog):
        caplog.set_level(logging.INFO)
        log_pipeline_end("T005", success=True, duration_seconds=10.5)
        assert "Task T005 completed with status: SUCCESS" in caplog.text
        assert "Duration: 10.50s" in caplog.text

    def test_log_pipeline_end_failure(self, caplog):
        caplog.set_level(logging.ERROR)
        log_pipeline_end("T005", success=False)
        assert "Task T005 completed with status: FAILED" in caplog.text