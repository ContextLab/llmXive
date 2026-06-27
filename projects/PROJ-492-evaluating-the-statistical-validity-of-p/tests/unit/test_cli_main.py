"""
Unit tests for the CLI interface skeleton.

These tests verify that the CLI responds correctly to --help
and other basic commands.
"""

import subprocess
import sys

def test_cli_help():
    """Verify that --help displays usage information."""
    result = subprocess.run(
        [sys.executable, "-m", "src.cli.main", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Help command failed: {result.stderr}"
    assert "abtest-audit" in result.stdout, "Help output missing program name"
    assert "statistical validity" in result.stdout.lower(), "Help missing description"

def test_cli_version():
    """Verify that --version displays version information."""
    result = subprocess.run(
        [sys.executable, "-m", "src.cli.main", "--version"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Version command failed: {result.stderr}"
    assert "0.1.0" in result.stdout, "Version output missing version string"

def test_cli_run_placeholder():
    """Verify that 'run' command executes without error."""
    result = subprocess.run(
        [sys.executable, "-m", "src.cli.main", "run"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Run command failed: {result.stderr}"
    assert "implementation in progress" in result.stdout.lower(), "Run command not placeholder"

def test_cli_module_importable():
    """Verify that the CLI module can be imported."""
    from src.cli.main import create_parser, main, __version__
    assert __version__ == "0.1.0", "Version mismatch"
    assert callable(create_parser), "create_parser not callable"
    assert callable(main), "main not callable"
