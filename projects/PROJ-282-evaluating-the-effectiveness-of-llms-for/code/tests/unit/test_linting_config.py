"""
Tests for the linting configuration verification.
"""
import json
import os
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
LOG_FILE = PROJECT_ROOT / "data" / "logs" / "linting_config.json"

def test_linting_log_exists():
    """Verify that the linting config log file was generated."""
    assert LOG_FILE.exists(), f"Log file {LOG_FILE} does not exist. Run verify_linting_config.py first."

def test_linting_log_is_valid_json():
    """Verify the log file contains valid JSON."""
    with open(LOG_FILE, "r") as f:
        data = json.load(f)
    assert isinstance(data, dict)

def test_linting_log_has_required_fields():
    """Verify the log file has the required structure."""
    with open(LOG_FILE, "r") as f:
        data = json.load(f)
    
    assert "timestamp" in data
    assert "overall_status" in data
    assert "checks" in data
    assert "ruff" in data["checks"]
    assert "black" in data["checks"]

def test_linting_tools_executed():
    """Verify that the linting tools were actually executed (return code present)."""
    with open(LOG_FILE, "r") as f:
        data = json.load(f)
    
    ruff_check = data["checks"]["ruff"]
    black_check = data["checks"]["black"]
    
    assert "returncode" in ruff_check
    assert "returncode" in black_check
    assert "command" in ruff_check
    assert "command" in black_check

def test_pyproject_toml_exists():
    """Verify pyproject.toml exists in project root."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml not found in project root"

def test_pyproject_contains_ruff_config():
    """Verify pyproject.toml contains ruff configuration."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    content = pyproject_path.read_text()
    assert "[tool.ruff]" in content, "ruff configuration missing in pyproject.toml"

def test_pyproject_contains_black_config():
    """Verify pyproject.toml contains black configuration."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    content = pyproject_path.read_text()
    assert "[tool.black]" in content, "black configuration missing in pyproject.toml"