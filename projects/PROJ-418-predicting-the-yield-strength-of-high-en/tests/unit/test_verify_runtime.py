"""
Unit tests for the runtime verification logic (T120).
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Import the function to test
from verify_runtime import verify_runtime

# We need to ensure the import path includes the project root
# In a real test runner, this would be handled by PYTHONPATH or conftest
# Here we assume the test is run from the project root


class TestVerifyRuntime:
    """Tests for the verify_runtime function."""

    def test_file_not_found(self, tmp_path, monkeypatch):
        """Test that verify_runtime returns False when the file is missing."""
        # Ensure the file does not exist
        runtime_file = tmp_path / "output" / "pipeline_runtime.json"
        runtime_file.parent.mkdir(parents=True, exist_ok=True)

        # Patch the path resolution to use tmp_path
        # The verify_runtime function uses a hardcoded path "output/pipeline_runtime.json"
        # We need to mock the Path.exists method or change the working directory
        # Changing the working directory is safer for this specific test structure
        monkeypatch.chdir(tmp_path)

        result = verify_runtime()
        assert result is False

    def test_invalid_json(self, tmp_path, monkeypatch):
        """Test that verify_runtime returns False for invalid JSON."""
        runtime_file = tmp_path / "output" / "pipeline_runtime.json"
        runtime_file.parent.mkdir(parents=True, exist_ok=True)
        runtime_file.write_text("this is not json")

        monkeypatch.chdir(tmp_path)

        result = verify_runtime()
        assert result is False

    def test_missing_fields(self, tmp_path, monkeypatch):
        """Test that verify_runtime returns False when required fields are missing."""
        runtime_file = tmp_path / "output" / "pipeline_runtime.json"
        runtime_file.parent.mkdir(parents=True, exist_ok=True)
        data = {"total_runtime_seconds": 100}  # Missing limit_seconds and status
        runtime_file.write_text(json.dumps(data))

        monkeypatch.chdir(tmp_path)

        result = verify_runtime()
        assert result is False

    def test_status_not_pass(self, tmp_path, monkeypatch):
        """Test that verify_runtime returns False when status is not 'pass'."""
        runtime_file = tmp_path / "output" / "pipeline_runtime.json"
        runtime_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "total_runtime_seconds": 100,
            "limit_seconds": 7200,
            "status": "fail"
        }
        runtime_file.write_text(json.dumps(data))

        monkeypatch.chdir(tmp_path)

        result = verify_runtime()
        assert result is False

    def test_exceeds_limit(self, tmp_path, monkeypatch):
        """Test that verify_runtime returns False when time exceeds limit."""
        runtime_file = tmp_path / "output" / "pipeline_runtime.json"
        runtime_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "total_runtime_seconds": 8000,
            "limit_seconds": 7200,
            "status": "pass"  # Even if status says pass, time check should fail
        }
        runtime_file.write_text(json.dumps(data))

        monkeypatch.chdir(tmp_path)

        result = verify_runtime()
        assert result is False

    def test_success(self, tmp_path, monkeypatch):
        """Test that verify_runtime returns True for a valid pass case."""
        runtime_file = tmp_path / "output" / "pipeline_runtime.json"
        runtime_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "total_runtime_seconds": 3600,
            "limit_seconds": 7200,
            "status": "pass"
        }
        runtime_file.write_text(json.dumps(data))

        monkeypatch.chdir(tmp_path)

        result = verify_runtime()
        assert result is True

    def test_exact_limit(self, tmp_path, monkeypatch):
        """Test that verify_runtime returns True when time equals limit."""
        runtime_file = tmp_path / "output" / "pipeline_runtime.json"
        runtime_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "total_runtime_seconds": 7200,
            "limit_seconds": 7200,
            "status": "pass"
        }
        runtime_file.write_text(json.dumps(data))

        monkeypatch.chdir(tmp_path)

        result = verify_runtime()
        assert result is True
