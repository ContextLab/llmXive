"""
Unit tests for code/utils.py utilities.
"""
import json
import os
import tempfile
from pathlib import Path

import pytest

from code.utils import (
    compute_file_checksum,
    ensure_file_directory,
    record_checksums,
    safe_json_load,
    safe_json_save,
    setup_logging,
)


class TestSetupLogging:
    def test_setup_logging_console_handler(self):
        logger = setup_logging(name="test_logger_console", level=20)
        assert logger.level == 20
        assert len(logger.handlers) >= 1
        # Verify a StreamHandler exists
        stream_handlers = [h for h in logger.handlers if isinstance(h, type(logging.StreamHandler()))]
        assert len(stream_handlers) > 0

    def test_setup_logging_file_handler(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "logs", "test.log")
            logger = setup_logging(name="test_logger_file", log_file=log_path)
            assert os.path.exists(log_path)
            file_handlers = [h for h in logger.handlers if isinstance(h, type(logging.FileHandler(log_path)))]
            # Check that a file handler was added (checking type name as direct instance check can be tricky with inheritance)
            assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)


class TestComputeFileChecksum:
    def test_compute_sha256(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data")
            tmp_path = tmp.name
        try:
            checksum = compute_file_checksum(tmp_path)
            assert len(checksum) == 64  # SHA256 hex length
            assert isinstance(checksum, str)
        finally:
            os.unlink(tmp_path)

    def test_compute_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            compute_file_checksum("nonexistent_file.txt")


class TestEnsureFileDirectory:
    def test_ensure_creates_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = os.path.join(tmpdir, "a", "b", "c", "file.txt")
            ensure_file_directory(nested_path)
            assert os.path.exists(os.path.join(tmpdir, "a", "b", "c"))

    def test_ensure_existing_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ensure_file_directory(tmpdir)
            assert os.path.exists(tmpdir)


class TestSafeJsonLoadSave:
    def test_save_and_load(self):
        data = {"key": "value", "number": 42}
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.json")
            safe_json_save(data, file_path)
            assert os.path.exists(file_path)

            loaded = safe_json_load(file_path)
            assert loaded == data

    def test_load_nonexistent(self):
        with pytest.raises(FileNotFoundError):
            safe_json_load("nonexistent.json")

    def test_save_default_str(self):
        data = {"date": Path("some/path")}
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.json")
            safe_json_save(data, file_path)
            loaded = safe_json_load(file_path)
            assert loaded["date"] == "some/path"


class TestRecordChecksums:
    def test_record_valid_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = os.path.join(tmpdir, "f1.txt")
            file2 = os.path.join(tmpdir, "f2.txt")
            with open(file1, "w") as f:
                f.write("content1")
            with open(file2, "w") as f:
                f.write("content2")

            output_path = os.path.join(tmpdir, "checksums.json")
            result = record_checksums([file1, file2], output_path)

            assert os.path.exists(output_path)
            assert file1 in result
            assert file2 in result
            assert result[file1] != "FILE_NOT_FOUND"
            assert result[file2] != "FILE_NOT_FOUND"

    def test_record_missing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            missing = os.path.join(tmpdir, "missing.txt")
            output_path = os.path.join(tmpdir, "checksums.json")
            result = record_checksums([missing], output_path)
            assert result[str(missing)] == "FILE_NOT_FOUND"
