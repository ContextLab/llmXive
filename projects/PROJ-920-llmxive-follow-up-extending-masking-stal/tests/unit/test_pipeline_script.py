"""
Unit tests for the run_pipeline.sh script functionality.
Validates that the script structure and error handling logic are correct.
"""
import os
import subprocess
import tempfile
import pytest
from pathlib import Path


class TestPipelineScript:
    """Tests for the run_pipeline.sh orchestration script."""

    @pytest.fixture
    def script_path(self):
        """Get the path to the run_pipeline.sh script."""
        return Path(__file__).parent.parent.parent / "run_pipeline.sh"

    def test_script_exists(self, script_path):
        """Verify that run_pipeline.sh exists in the project root."""
        assert script_path.exists(), "run_pipeline.sh must exist in the project root"

    def test_script_is_executable(self, script_path):
        """Verify that run_pipeline.sh has executable permissions."""
        assert os.access(script_path, os.X_OK), "run_pipeline.sh must be executable"

    def test_script_syntax(self, script_path):
        """Verify that the bash script has valid syntax."""
        result = subprocess.run(
            ["bash", "-n", str(script_path)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Script syntax error: {result.stderr}"

    def test_script_contains_required_steps(self, script_path):
        """Verify that the script calls all required Python scripts."""
        content = script_path.read_text()

        required_scripts = [
            "generate_trajectories.py",
            "simulate_agent.py",
            "analyze_results.py",
            "visualize_results.py"
        ]

        for script in required_scripts:
            assert script in content, f"Script must call {script}"

    def test_script_contains_error_handling(self, script_path):
        """Verify that the script includes error handling (set -e)."""
        content = script_path.read_text()
        assert "set -e" in content, "Script must include 'set -e' for error handling"

    def test_script_logs_exit_codes(self, script_path):
        """Verify that the script logs exit codes on failure."""
        content = script_path.read_text()
        assert "exit_code" in content.lower() or "returncode" in content.lower(), \
            "Script must log exit codes on failure"

    def test_script_stops_on_failure(self, script_path):
        """Verify that the script stops execution on failure."""
        content = script_path.read_text()
        # Check for logic that exits on non-zero return
        assert "exit" in content.lower() or "returncode" in content.lower(), \
            "Script must stop execution on failure"

    def test_script_output_paths(self, script_path):
        """Verify that the script uses the correct output paths."""
        content = script_path.read_text()

        required_paths = [
            "data/raw/trajectories.json",
            "data/processed/simulation_results.csv",
            "output/regression_summary.json",
            "output/hypothesis_summary.md",
            "output/plots/regime_map.png"
        ]

        for path in required_paths:
            assert path in content, f"Script must reference output path: {path}"

    def test_script_has_logging(self, script_path):
        """Verify that the script includes logging functionality."""
        content = script_path.read_text()
        assert "log" in content.lower() or "tee" in content, \
            "Script must include logging functionality"