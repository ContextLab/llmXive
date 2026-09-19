"""
Contract tests for the Feasibility Gate Enforcer (T001c).

These tests verify the logic of the feasibility gate enforcer without
actually executing the full pipeline or modifying global state permanently.
"""
import os
import sys
import yaml
import tempfile
import subprocess
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.utils.logger import setup_logging_for_task, close_logging

GATE_STATUS_FILENAME = "feasibility_gate_status.yaml"
GATE_STATUS_DIR = Path("data/processed")

def setup_module(module):
    """Ensure the data/processed directory exists for tests."""
    GATE_STATUS_DIR.mkdir(parents=True, exist_ok=True)

def teardown_module(module):
    """Clean up logging and temporary files if necessary."""
    close_logging()

def create_status_file(status_value: str):
    """Helper to create a temporary status file for testing."""
    status_path = GATE_STATUS_DIR / GATE_STATUS_FILENAME
    data = {"status": status_value}
    with open(status_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f)
    return status_path

def remove_status_file():
    """Helper to remove the status file."""
    status_path = GATE_STATUS_DIR / GATE_STATUS_FILENAME
    if status_path.exists():
        status_path.unlink()

@pytest.fixture
def status_file_pass():
    path = create_status_file("PASS")
    yield path
    remove_status_file()

@pytest.fixture
def status_file_fail():
    path = create_status_file("FAIL")
    yield path
    remove_status_file()

@pytest.fixture
def status_file_missing():
    # Ensure file does not exist
    remove_status_file()
    yield None

@pytest.fixture
def status_file_invalid():
    path = GATE_STATUS_DIR / GATE_STATUS_FILENAME
    with open(path, 'w', encoding='utf-8') as f:
        f.write("invalid: yaml: content: [")
    yield path
    remove_status_file()

def test_gate_pass_exits_zero(status_file_pass):
    """Test that a PASS status results in exit code 0."""
    # Run the script as a subprocess to capture exit code cleanly
    script_path = Path("src/ingestion/feasibility_gate_enforcer.py")
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}. Stderr: {result.stderr}"
    assert "Feasibility Gate: PASS" in result.stdout

def test_gate_fail_exits_one(status_file_fail):
    """Test that a FAIL status results in exit code 1."""
    script_path = Path("src/ingestion/feasibility_gate_enforcer.py")
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}. Stderr: {result.stderr}"
    assert "Feasibility Gate Failed: Halting pipeline." in result.stderr

def test_gate_missing_file_exits_one(status_file_missing):
    """Test that a missing status file results in exit code 1."""
    script_path = Path("src/ingestion/feasibility_gate_enforcer.py")
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}. Stderr: {result.stderr}"
    assert "Status file missing" in result.stderr

def test_gate_invalid_yaml_exits_one(status_file_invalid):
    """Test that invalid YAML in status file results in exit code 1."""
    script_path = Path("src/ingestion/feasibility_gate_enforcer.py")
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}. Stderr: {result.stderr}"
    assert "YAML parsing error" in result.stderr

def test_gate_unknown_status_exits_one(tmp_path):
    """Test that an unknown status value results in exit code 1."""
    # Create a temporary status file with unknown value
    status_path = GATE_STATUS_DIR / GATE_STATUS_FILENAME
    with open(status_path, 'w', encoding='utf-8') as f:
        yaml.dump({"status": "UNKNOWN_VALUE"}, f)
    
    try:
        script_path = Path("src/ingestion/feasibility_gate_enforcer.py")
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}. Stderr: {result.stderr}"
        assert "Unknown status value" in result.stderr
    finally:
        remove_status_file()