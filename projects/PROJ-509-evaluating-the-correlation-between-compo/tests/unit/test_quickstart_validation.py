"""
Unit tests for the quickstart_validation module.
"""

import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module functions to test
# We need to adjust the import path based on how tests are run
# Assuming tests are run from project root or with proper PYTHONPATH
try:
    from code.quickstart_validation import run_step, verify_artifacts, validate_metrics_content
except ImportError:
    # Fallback for different execution contexts
    from quickstart_validation import run_step, verify_artifacts, validate_metrics_content


class TestRunStep:
    def test_run_step_success(self):
        """Test run_step with a command that succeeds."""
        # Use a simple command that should always succeed
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="success", stderr="")
            result = run_step("Test Step", ["echo", "hello"])
            assert result is True
            mock_run.assert_called_once()

    def test_run_step_failure(self):
        """Test run_step with a command that fails."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
            result = run_step("Test Step", ["false"])
            assert result is False

    def test_run_step_file_not_found(self):
        """Test run_step when command is not found."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("Command not found")
            result = run_step("Test Step", ["nonexistent_command"])
            assert result is False


class TestVerifyArtifacts:
    def test_all_artifacts_present(self, tmp_path):
        """Test verify_artifacts when all files exist."""
        # Create dummy files
        (tmp_path / "file1.txt").touch()
        (tmp_path / "file2.txt").touch()

        artifacts = {
            "File 1": "file1.txt",
            "File 2": "file2.txt"
        }

        result = verify_artifacts(artifacts, tmp_path)
        assert result is True

    def test_missing_artifact(self, tmp_path):
        """Test verify_artifacts when a file is missing."""
        (tmp_path / "file1.txt").touch()

        artifacts = {
            "File 1": "file1.txt",
            "File 2": "missing.txt"
        }

        result = verify_artifacts(artifacts, tmp_path)
        assert result is False

    def test_empty_artifact(self, tmp_path):
        """Test verify_artifacts when a file exists but is empty."""
        # Create an empty file
        (tmp_path / "file1.txt").touch()
        # Create a non-empty file
        (tmp_path / "file2.txt").write_text("content")

        artifacts = {
            "File 1": "file1.txt",
            "File 2": "file2.txt"
        }

        # The function logs a warning but returns False for empty files
        result = verify_artifacts(artifacts, tmp_path)
        assert result is False


class TestValidateMetricsContent:
    def test_valid_metrics(self, tmp_path):
        """Test validate_metrics_content with valid data."""
        metrics_file = tmp_path / "model_metrics.json"
        valid_data = {
            "rf_r2": 0.85,
            "gb_r2": 0.88,
            "rf_mae": 0.1,
            "gb_mae": 0.09,
            "rf_rmse": 0.15,
            "gb_rmse": 0.14
        }
        metrics_file.write_text(json.dumps(valid_data))

        result = validate_metrics_content(metrics_file)
        assert result is True

    def test_missing_keys(self, tmp_path):
        """Test validate_metrics_content with missing keys."""
        metrics_file = tmp_path / "model_metrics.json"
        invalid_data = {
            "rf_r2": 0.85,
            "gb_r2": 0.88
            # Missing other required keys
        }
        metrics_file.write_text(json.dumps(invalid_data))

        result = validate_metrics_content(metrics_file)
        assert result is False

    def test_non_numeric_values(self, tmp_path):
        """Test validate_metrics_content with non-numeric values."""
        metrics_file = tmp_path / "model_metrics.json"
        invalid_data = {
            "rf_r2": "not_a_number",
            "gb_r2": 0.88,
            "rf_mae": 0.1,
            "gb_mae": 0.09,
            "rf_rmse": 0.15,
            "gb_rmse": 0.14
        }
        metrics_file.write_text(json.dumps(invalid_data))

        result = validate_metrics_content(metrics_file)
        assert result is False

    def test_invalid_json(self, tmp_path):
        """Test validate_metrics_content with invalid JSON."""
        metrics_file = tmp_path / "model_metrics.json"
        metrics_file.write_text("{ invalid json }")

        result = validate_metrics_content(metrics_file)
        assert result is False
