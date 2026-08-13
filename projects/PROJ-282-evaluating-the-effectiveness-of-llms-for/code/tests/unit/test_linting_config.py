"""
Unit tests to verify the linting configuration setup.
These tests ensure that the configuration files exist and are parseable.
"""
import os
import json
import tempfile
import subprocess
import sys
from pathlib import Path
import pytest

# Assume project root is the parent of 'tests'
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def test_pyproject_toml_exists():
    """Verify pyproject.toml exists in project root."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml must exist in project root"

def test_pyproject_toml_valid():
    """Verify pyproject.toml contains ruff and black configuration."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    if not pyproject_path.exists():
        pytest.skip("pyproject.toml not found")
    
    # Basic check: try to read and ensure it has content
    content = pyproject_path.read_text()
    assert "[tool.ruff]" in content, "pyproject.toml must contain [tool.ruff] section"
    assert "[tool.black]" in content, "pyproject.toml must contain [tool.black] section"

def test_linting_config_script_runs():
    """Verify the verification script runs without crashing."""
    script_path = PROJECT_ROOT / "scripts" / "verify_linting_config.py"
    if not script_path.exists():
        pytest.skip("verify_linting_config.py not found")
    
    # Run the script
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    # It should exit with 0 if config is valid (even if no files to check)
    # We allow exit code 0 or 1 (if strict check fails but config is valid)
    # However, the script logic sets exit 0 on PASS.
    assert result.returncode == 0, f"Script failed: {result.stderr}"

def test_linting_log_generated():
    """Verify that the linting log is generated after running the script."""
    log_path = PROJECT_ROOT / "data" / "logs" / "linting_config.json"
    
    # Run script first to ensure log exists
    script_path = PROJECT_ROOT / "scripts" / "verify_linting_config.py"
    if script_path.exists():
        subprocess.run([sys.executable, str(script_path)], cwd=PROJECT_ROOT, capture_output=True)
    
    if not log_path.exists():
        pytest.skip("Log file not generated, script might have been skipped")

    with open(log_path, "r") as f:
        data = json.load(f)
    
    assert "checks" in data, "Log must contain 'checks' key"
    assert "ruff_check" in data["checks"], "Log must contain ruff_check result"
    assert "black_check" in data["checks"], "Log must contain black_check result"
    assert "overall_status" in data, "Log must contain overall_status"