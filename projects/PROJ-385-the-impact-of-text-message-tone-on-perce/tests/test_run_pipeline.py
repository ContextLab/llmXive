"""Tests for the run_pipeline CLI."""

import subprocess
import sys
from pathlib import Path

def test_help_output():
    """The ``--help`` flag must display usage information."""
    result = subprocess.run(
        [sys.executable, "code/run_pipeline.py", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Project pipeline entry point" in result.stdout

def test_mode_real():
    """Running with ``--mode real`` must exit with status 0."""
    result = subprocess.run(
        [sys.executable, "code/run_pipeline.py", "--mode", "real"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Running full pipeline" in result.stdout

def test_mode_benchmark():
    """Running with ``--mode benchmark`` must exit with status 0."""
    result = subprocess.run(
        [sys.executable, "code/run_pipeline.py", "--mode", "benchmark"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Running benchmark" in result.stdout