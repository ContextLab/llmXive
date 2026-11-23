"""test_cli_guard.py

Contract test for the Primary Pipeline CLI guard clauses.

Verifies that:
  1. ``--mode mock`` with ``--generate-report`` exits with code 1
     and the message: "Mock mode is not allowed for primary analysis; real data is required."
  2. ``--mode real`` executes successfully (placeholder check).
  3. ``--mode benchmark`` executes successfully (placeholder check).
"""

import subprocess
import sys
import pytest
from pathlib import Path

# Get the project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"

def test_mock_mode_with_generate_report_fails():
    """Test that --mode mock with --generate-report exits with code 1."""
    result = subprocess.run(
        [sys.executable, str(CODE_DIR / "run_pipeline.py"), "--mode", "mock", "--generate-report"],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )

    # Verify exit code is 1
    assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}. Stderr: {result.stderr}"

    # Verify error message
    expected_msg = "Mock mode is not allowed for primary analysis; real data is required."
    assert expected_msg in result.stdout or expected_msg in result.stderr, (
        f"Expected message not found. stdout: {result.stdout}, stderr: {result.stderr}"
    )

def test_real_mode_executes():
    """Test that --mode real executes without syntax errors."""
    result = subprocess.run(
        [sys.executable, str(CODE_DIR / "run_pipeline.py"), "--mode", "real"],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )

    # Should not have a syntax error or import error preventing execution
    # The actual pipeline may fail due to missing data, but the CLI should parse correctly
    assert "SyntaxError" not in result.stderr, f"Syntax error detected: {result.stderr}"
    assert "ImportError" not in result.stderr or "No module named" not in result.stderr, (
        f"Import error detected: {result.stderr}"
    )

def test_benchmark_mode_executes():
    """Test that --mode benchmark executes without syntax errors."""
    result = subprocess.run(
        [sys.executable, str(CODE_DIR / "run_pipeline.py"), "--mode", "benchmark"],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )

    assert "SyntaxError" not in result.stderr, f"Syntax error detected: {result.stderr}"
    assert "ImportError" not in result.stderr or "No module named" not in result.stderr, (
        f"Import error detected: {result.stderr}"
    )

def test_help_flag_works():
    """Test that --help displays usage information."""
    result = subprocess.run(
        [sys.executable, str(CODE_DIR / "run_pipeline.py"), "--help"],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )

    assert result.returncode == 0, f"Help flag failed with code {result.returncode}"
    assert "mode" in result.stdout.lower(), "Help output should mention '--mode'"
