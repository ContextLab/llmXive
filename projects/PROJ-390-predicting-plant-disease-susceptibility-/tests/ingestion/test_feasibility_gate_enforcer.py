"""
Tests for the Feasibility Gate Enforcer (T001c).

These tests verify that the enforcer correctly reads the gate status file
and exits with the appropriate code (0 for PASS, 1 for FAIL).
"""
import os
import sys
import tempfile
import yaml
from pathlib import Path
import subprocess

import pytest

# Add the project root to the path if running directly
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.feasibility_gate_enforcer import main as enforcer_main
from src.utils.logger import setup_logging_for_task

# We will test the main function logic by mocking the file system
# or by running the script in a subprocess with temporary files.

@pytest.fixture
def temp_data_dir(tmp_path):
    """Creates a temporary directory structure mimicking data/processed/"""
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    return processed_dir

def test_gate_pass(tmp_path, capsys):
    """Test that the enforcer exits with 0 when status is PASS."""
    # Create the gate status file
    status_file = tmp_path / "data" / "processed" / "feasibility_gate_status.yaml"
    status_file.parent.mkdir(parents=True, exist_ok=True)
    status_file.write_text("status: PASS\n")

    # Run the enforcer logic
    # We need to temporarily change the constant or mock the path
    # Since the constant is hardcoded, we will run the script via subprocess
    # or patch the module. Let's use subprocess for a more realistic test.
    
    # Prepare a script that sets the path dynamically or we patch the module
    # For simplicity in unit testing the logic, we will patch the module's path
    import src.ingestion.feasibility_gate_enforcer as module
    
    original_path = module.GATE_STATUS_FILE
    try:
        module.GATE_STATUS_FILE = status_file
        exit_code = enforcer_main()
        assert exit_code == 0
    finally:
        module.GATE_STATUS_FILE = original_path

def test_gate_fail(tmp_path, capsys):
    """Test that the enforcer exits with 1 when status is FAIL."""
    status_file = tmp_path / "data" / "processed" / "feasibility_gate_status.yaml"
    status_file.parent.mkdir(parents=True, exist_ok=True)
    status_file.write_text("status: FAIL\n")

    import src.ingestion.feasibility_gate_enforcer as module
    original_path = module.GATE_STATUS_FILE
    try:
        module.GATE_STATUS_FILE = status_file
        exit_code = enforcer_main()
        assert exit_code == 1
    finally:
        module.GATE_STATUS_FILE = original_path

def test_gate_missing_file(tmp_path, capsys):
    """Test that the enforcer exits with 1 when the status file is missing."""
    # Create the directory but not the file
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    import src.ingestion.feasibility_gate_enforcer as module
    original_path = module.GATE_STATUS_FILE
    try:
        module.GATE_STATUS_FILE = processed_dir / "non_existent.yaml"
        exit_code = enforcer_main()
        assert exit_code == 1
    finally:
        module.GATE_STATUS_FILE = original_path

def test_gate_invalid_yaml(tmp_path, capsys):
    """Test that the enforcer exits with 1 when the YAML is invalid."""
    status_file = tmp_path / "data" / "processed" / "feasibility_gate_status.yaml"
    status_file.parent.mkdir(parents=True, exist_ok=True)
    status_file.write_text("this is not valid yaml: [\n")

    import src.ingestion.feasibility_gate_enforcer as module
    original_path = module.GATE_STATUS_FILE
    try:
        module.GATE_STATUS_FILE = status_file
        exit_code = enforcer_main()
        assert exit_code == 1
    finally:
        module.GATE_STATUS_FILE = original_path

def test_gate_missing_status_key(tmp_path, capsys):
    """Test that the enforcer exits with 1 when the 'status' key is missing."""
    status_file = tmp_path / "data" / "processed" / "feasibility_gate_status.yaml"
    status_file.parent.mkdir(parents=True, exist_ok=True)
    status_file.write_text("other_key: value\n")

    import src.ingestion.feasibility_gate_enforcer as module
    original_path = module.GATE_STATUS_FILE
    try:
        module.GATE_STATUS_FILE = status_file
        exit_code = enforcer_main()
        assert exit_code == 1
    finally:
        module.GATE_STATUS_FILE = original_path

def test_gate_unknown_status(tmp_path, capsys):
    """Test that the enforcer exits with 1 when the status value is unknown."""
    status_file = tmp_path / "data" / "processed" / "feasibility_gate_status.yaml"
    status_file.parent.mkdir(parents=True, exist_ok=True)
    status_file.write_text("status: UNKNOWN\n")

    import src.ingestion.feasibility_gate_enforcer as module
    original_path = module.GATE_STATUS_FILE
    try:
        module.GATE_STATUS_FILE = status_file
        exit_code = enforcer_main()
        assert exit_code == 1
    finally:
        module.GATE_STATUS_FILE = original_path