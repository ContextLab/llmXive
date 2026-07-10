"""
Unit tests for the quickstart validation logic.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from validation.run_quickstart_check import check_file_exists, run_command


class TestCheckFileExists:
    def test_existing_non_empty_file(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        assert check_file_exists(test_file, "test") is True

    def test_missing_file(self, tmp_path):
        missing_file = tmp_path / "missing.txt"
        assert check_file_exists(missing_file, "test") is False

    def test_empty_file(self, tmp_path):
        empty_file = tmp_path / "empty.txt"
        empty_file.touch()
        assert check_file_exists(empty_file, "test") is False


class TestRunCommand:
    def test_successful_command(self):
        success, stdout, stderr = run_command([sys.executable, "-c", "print('hello')"])
        assert success is True
        assert "hello" in stdout
        assert stderr == ""

    def test_failed_command(self):
        success, stdout, stderr = run_command([sys.executable, "-c", "exit(1)"])
        assert success is False

    def test_timeout(self):
        success, stdout, stderr = run_command([sys.executable, "-c", "import time; time.sleep(10)"], timeout=1)
        assert success is False
        assert "timed out" in stderr