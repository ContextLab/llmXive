"""
Integration tests for T036: Quickstart Validator
"""
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

# Add code directory to path
CODE_DIR = Path(__file__).resolve().parent.parent.parent / "code"
sys.path.insert(0, str(CODE_DIR))

from quickstart_validator import run_command, validate_quickstart
from utils.logger import setup_logging

@pytest.fixture
def logger():
    return setup_logging(level="DEBUG")

class TestRunCommand:
    def test_run_command_success(self, logger, tmp_path):
        """Test that run_command returns True for successful commands."""
        # Create a simple script that exits 0
        script = tmp_path / "success.sh"
        script.write_text("#!/bin/bash\nexit 0")
        script.chmod(0o755)

        assert run_command([str(script)], logger, check=True) is True

    def test_run_command_failure(self, logger, tmp_path):
        """Test that run_command returns False for failed commands."""
        # Create a simple script that exits 1
        script = tmp_path / "fail.sh"
        script.write_text("#!/bin/bash\nexit 1")
        script.chmod(0o755)

        # We expect check=True to raise, so we handle it in the function
        # The function catches CalledProcessError and returns False
        assert run_command([str(script)], logger, check=True) is False

    def test_run_command_nonexistent(self, logger):
        """Test that run_command returns False for non-existent commands."""
        assert run_command(["nonexistent_command_xyz"], logger, check=True) is False

class TestValidateQuickstart:
    def test_validate_missing_dirs(self, logger, tmp_path):
        """Test validation fails when directories are missing."""
        # Mock PROJECT_ROOT to point to a temp directory
        with patch("quickstart_validator.PROJECT_ROOT", tmp_path):
            with patch("quickstart_validator.CODE_DIR", tmp_path / "code"):
                with patch("quickstart_validator.DATA_DIR", tmp_path / "data"):
                    # Directories don't exist, should fail immediately
                    result = validate_quickstart(logger)
                    assert result is False

    def test_validate_mocked_pipeline(self, logger, tmp_path):
        """Test validation passes when all pipeline steps are mocked to succeed."""
        # Setup temp structure
        code_dir = tmp_path / "code"
        data_dir = tmp_path / "data"
        code_dir.mkdir()
        data_dir.mkdir()
        (data_dir / "raw").mkdir()
        (data_dir / "intermediates" / "raw_logs").mkdir(parents=True)
        (data_dir / "results").mkdir()
        (code_dir / "kernels").mkdir()
        (code_dir / "benchmarks").mkdir()
        (code_dir / "analysis").mkdir()
        (code_dir / "utils").mkdir()

        # Create dummy output files
        (data_dir / "results" / "aggregated.csv").touch()
        (data_dir / "results" / "pareto_frontier_final.png").touch()
        (data_dir / "results" / "pareto_frontier_exploration.png").touch()
        (data_dir / "manifest.json").touch()

        # Mock run_command to always return True
        with patch("quickstart_validator.PROJECT_ROOT", tmp_path):
            with patch("quickstart_validator.CODE_DIR", code_dir):
                with patch("quickstart_validator.DATA_DIR", data_dir):
                    with patch("quickstart_validator.run_command", return_value=True):
                        result = validate_quickstart(logger)
                        assert result is True

    def test_validate_pipeline_step_failure(self, logger, tmp_path):
        """Test validation fails if a pipeline step fails."""
        # Setup temp structure
        code_dir = tmp_path / "code"
        data_dir = tmp_path / "data"
        code_dir.mkdir()
        data_dir.mkdir()
        (data_dir / "raw").mkdir()
        (data_dir / "intermediates" / "raw_logs").mkdir(parents=True)
        (data_dir / "results").mkdir()
        (code_dir / "kernels").mkdir()
        (code_dir / "benchmarks").mkdir()
        (code_dir / "analysis").mkdir()
        (code_dir / "utils").mkdir()

        # Create dummy output files (to pass the final check, we need them)
        (data_dir / "results" / "aggregated.csv").touch()
        (data_dir / "results" / "pareto_frontier_final.png").touch()
        (data_dir / "results" / "pareto_frontier_exploration.png").touch()
        (data_dir / "manifest.json").touch()

        # Mock run_command to fail on the 3rd call (compile step)
        call_count = 0
        def mock_run_fail(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 3:
                return False
            return True

        with patch("quickstart_validator.PROJECT_ROOT", tmp_path):
            with patch("quickstart_validator.CODE_DIR", code_dir):
                with patch("quickstart_validator.DATA_DIR", data_dir):
                    with patch("quickstart_validator.run_command", side_effect=mock_run_fail):
                        result = validate_quickstart(logger)
                        assert result is False
                        # Ensure it stopped at the failure
                        assert call_count == 3