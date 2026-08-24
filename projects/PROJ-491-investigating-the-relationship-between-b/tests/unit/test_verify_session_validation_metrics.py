"""
Unit tests for verify_session_validation_metrics.py (Task T013d).
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# We will test the logic by mocking the file system or passing a mock path
# Since the script uses a global path, we need to test the logic function directly
# by importing it or refactoring slightly for testability.
# For this task, we assume the logic is robust and test the file I/O behavior.

from verify_session_validation_metrics import verify_metrics_file, REQUIRED_KEYS

def test_verify_missing_file():
    """Test that verification fails when file is missing."""
    # Temporarily rename the file if it exists to simulate missing state
    # Or we can test by changing the global variable in the module (monkeypatch)
    # Since verify_metrics_file uses a global METRICS_FILE_PATH, we monkeypatch it.
    import verify_session_validation_metrics as module
    original_path = module.METRICS_FILE_PATH
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_path = Path(tmpdir) / "nonexistent.json"
            module.METRICS_FILE_PATH = fake_path
            assert verify_metrics_file() is False
    finally:
        module.METRICS_FILE_PATH = original_path

def test_verify_invalid_json(tmp_path):
    """Test that verification fails on invalid JSON."""
    import verify_session_validation_metrics as module
    original_path = module.METRICS_FILE_PATH
    try:
        fake_file = tmp_path / "metrics.json"
        fake_file.write_text("{ invalid json }")
        module.METRICS_FILE_PATH = fake_file
        assert verify_metrics_file() is False
    finally:
        module.METRICS_FILE_PATH = original_path

def test_verify_missing_keys(tmp_path):
    """Test that verification fails on missing keys."""
    import verify_session_validation_metrics as module
    original_path = module.METRICS_FILE_PATH
    try:
        fake_file = tmp_path / "metrics.json"
        fake_file.write_text(json.dumps({"pass_rate": 0.5}))
        module.METRICS_FILE_PATH = fake_file
        assert verify_metrics_file() is False
    finally:
        module.METRICS_FILE_PATH = original_path

def test_verify_invalid_types(tmp_path):
    """Test that verification fails on invalid types."""
    import verify_session_validation_metrics as module
    original_path = module.METRICS_FILE_PATH
    try:
        fake_file = tmp_path / "metrics.json"
        # pass_rate should be number, total_subjects int, valid_subjects int
        fake_file.write_text(json.dumps({
            "pass_rate": "0.5",  # string instead of number
            "total_subjects": 50,
            "valid_subjects": 40
        }))
        module.METRICS_FILE_PATH = fake_file
        assert verify_metrics_file() is False
    finally:
        module.METRICS_FILE_PATH = original_path

def test_verify_success(tmp_path):
    """Test that verification succeeds with valid data."""
    import verify_session_validation_metrics as module
    original_path = module.METRICS_FILE_PATH
    try:
        fake_file = tmp_path / "metrics.json"
        fake_file.write_text(json.dumps({
            "pass_rate": 0.85,
            "total_subjects": 50,
            "valid_subjects": 43
        }))
        module.METRICS_FILE_PATH = fake_file
        assert verify_metrics_file() is True
    finally:
        module.METRICS_FILE_PATH = original_path
