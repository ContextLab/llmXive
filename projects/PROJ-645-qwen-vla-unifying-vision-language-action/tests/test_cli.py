"""
Unit tests for the base CLI entry point (T005).

Verifies that the argument parser correctly handles the --ratio argument
and that the CLI structure is valid.
"""
import pytest
from click.testing import CliRunner
import os
import tempfile
import shutil

# Import the CLI module
# Adjust import path based on project structure (src/cli.py)
import sys
import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.cli import cli


class TestCLI:
    def test_cli_help(self):
        """Test that the CLI help command works."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Qwen-VLA Cross-Embodiment Transfer Study CLI" in result.output

    def test_run_default_ratio(self):
        """Test the run command with default ratio (1.0)."""
        runner = CliRunner()
        result = runner.invoke(cli, ["run"])
        assert result.exit_code == 0
        assert "Data Ratio: 1.0" in result.output

    def test_run_custom_ratio(self):
        """Test the run command with a custom ratio (0.5)."""
        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--ratio", "0.5"])
        assert result.exit_code == 0
        assert "Data Ratio: 0.5" in result.output

    def test_run_invalid_ratio_high(self):
        """Test that a ratio > 1.0 raises an error."""
        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--ratio", "1.5"])
        assert result.exit_code != 0
        assert "Ratio must be between 0.0 and 1.0" in result.output

    def test_run_invalid_ratio_low(self):
        """Test that a ratio < 0.0 raises an error."""
        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--ratio", "-0.1"])
        assert result.exit_code != 0
        assert "Ratio must be between 0.0 and 1.0" in result.output

    def test_run_output_dir_creation(self):
        """Test that the output directory is created if it doesn't exist."""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            test_output_dir = os.path.join(tmpdir, "test_output")
            assert not os.path.exists(test_output_dir)

            result = runner.invoke(cli, ["run", "--output-dir", test_output_dir])
            
            assert result.exit_code == 0
            assert os.path.exists(test_output_dir)
            assert "Created output directory" in result.output

    def test_version_command(self):
        """Test the version command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["version"])
        assert result.exit_code == 0
        assert "v0.1.0" in result.output