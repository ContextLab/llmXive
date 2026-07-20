"""
Integration test for the run_all_tests.sh script.
This test verifies that the shell script exists, is executable, and
contains the expected commands for the three main test phases.
"""
import os
import subprocess
import stat
import pytest
from pathlib import Path

@pytest.fixture
def script_path():
    return Path(__file__).parent.parent / "code" / "run_all_tests.sh"

def test_script_exists(script_path):
    """Verify the script file exists."""
    assert script_path.exists(), f"Script not found at {script_path}"

def test_script_executable(script_path):
    """Verify the script has executable permissions."""
    mode = script_path.stat().st_mode
    assert mode & stat.S_IXUSR, f"Script {script_path} is not executable"

def test_script_content_structure(script_path):
    """Verify the script contains the required test phases."""
    content = script_path.read_text()

    # Check for shebang
    assert content.startswith("#!/bin/bash"), "Missing shebang"

    # Check for testthat execution
    assert "testthat::test_dir" in content, "Missing testthat execution"

    # Check for benchmark accuracy test
    assert "06_benchmark_accuracy.R" in content, "Missing benchmark accuracy test"
    assert "--mode=test" in content, "Missing test mode flag for benchmark"

    # Check for report rendering
    assert "04_report.Rmd" in content, "Missing report rendering step"
    assert "schema_check.csv" in content, "Missing test data input reference"

def test_script_syntax(script_path):
    """Verify the script has valid bash syntax."""
    result = subprocess.run(
        ["bash", "-n", str(script_path)],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Syntax error in script: {result.stderr}"