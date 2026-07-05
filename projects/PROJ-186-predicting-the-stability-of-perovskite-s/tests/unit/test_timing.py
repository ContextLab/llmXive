"""
Unit tests for pipeline timing validation (Task T042).
"""
import pytest
import time
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.timing import (
    run_pipeline_script,
    run_full_pipeline_validation,
    MAX_RUNTIME_SECONDS,
    PIPELINE_SCRIPTS,
)

class TestPipelineTiming:
    """Tests for pipeline timing validation functions."""

    def test_max_runtime_constant(self):
        """Verify the 6-hour limit is correctly set."""
        assert MAX_RUNTIME_SECONDS == 6 * 60 * 60
        assert MAX_RUNTIME_SECONDS == 21600

    def test_pipeline_scripts_list_not_empty(self):
        """Verify we have scripts to test."""
        assert len(PIPELINE_SCRIPTS) > 0
        assert all(isinstance(s, str) for s in PIPELINE_SCRIPTS)

    @patch("utils.timing.subprocess.run")
    @patch("utils.timing.logger")
    def test_run_pipeline_script_success(self, mock_logger, mock_subprocess):
        """Test successful script execution timing."""
        # Setup mock
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "output"
        mock_process.stderr = ""
        mock_subprocess.return_value = mock_process

        # Mock Path.exists to return True
        with patch("utils.timing.Path.exists", return_value=True):
            result = run_pipeline_script("code/data/download.py", dry_run=False)

        assert result["status"] == "success"
        assert result["runtime_seconds"] >= 0
        assert "script" in result

    @patch("utils.timing.subprocess.run")
    @patch("utils.timing.logger")
    def test_run_pipeline_script_failure(self, mock_logger, mock_subprocess):
        """Test failed script execution handling."""
        # Setup mock
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stdout = ""
        mock_process.stderr = "Error occurred"
        mock_subprocess.return_value = mock_process

        with patch("utils.timing.Path.exists", return_value=True):
            result = run_pipeline_script("code/data/download.py", dry_run=False)

        assert result["status"] == "failed"
        assert result["return_code"] == 1

    @patch("utils.timing.Path.exists", return_value=False)
    def test_run_pipeline_script_missing(self, mock_exists):
        """Test handling of missing script files."""
        result = run_pipeline_script("nonexistent.py", dry_run=False)
        assert result["status"] == "skipped"
        assert result["reason"] == "file_not_found"

    def test_run_pipeline_script_dry_run(self):
        """Test dry run mode."""
        with patch("utils.timing.Path.exists", return_value=True):
            result = run_pipeline_script("code/data/download.py", dry_run=True)
        
        assert result["status"] == "dry_run"
        assert result["runtime_seconds"] == 0

    @patch("utils.timing.run_pipeline_script")
    def test_run_full_pipeline_validation_success(self, mock_run_script):
        """Test full pipeline validation with all successes."""
        # Mock all scripts to succeed with 1 second each
        mock_run_script.side_effect = [
            {
                "script": f"script_{i}.py",
                "status": "success",
                "runtime_seconds": 1.0,
            }
            for i in range(len(PIPELINE_SCRIPTS))
        ]

        summary = run_full_pipeline_validation(dry_run=False)

        assert summary["total_runtime_seconds"] == len(PIPELINE_SCRIPTS) * 1.0
        assert summary["success_count"] == len(PIPELINE_SCRIPTS)
        assert len(summary["failed_scripts"]) == 0

    @patch("utils.timing.run_pipeline_script")
    def test_run_full_pipeline_validation_with_failures(self, mock_run_script):
        """Test full pipeline validation with some failures."""
        def side_effect(script, dry_run=False):
            if "train.py" in script:
                return {
                    "script": script,
                    "status": "failed",
                    "runtime_seconds": 10.0,
                    "return_code": 1,
                }
            return {
                "script": script,
                "status": "success",
                "runtime_seconds": 1.0,
            }

        mock_run_script.side_effect = side_effect

        summary = run_full_pipeline_validation(dry_run=False)

        assert summary["failed_scripts"] == ["code/models/train.py"]
        assert summary["success_count"] == len(PIPELINE_SCRIPTS) - 1

    @patch("utils.timing.run_pipeline_script")
    def test_runtime_exceeds_limit(self, mock_run_script):
        """Test detection of runtime exceeding 6-hour limit."""
        # Mock scripts to take 7 hours total
        mock_run_script.side_effect = [
            {
                "script": f"script_{i}.py",
                "status": "success",
                "runtime_seconds": 7 * 3600 / len(PIPELINE_SCRIPTS),
            }
            for i in range(len(PIPELINE_SCRIPTS))
        ]

        summary = run_full_pipeline_validation(dry_run=False)

        assert summary["total_runtime_hours"] > 6.0
        assert summary["passed"] is False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
