import os
import json
import pytest
from pathlib import Path

def test_directories_exist():
    """Verify that the required project directories exist."""
    base_path = Path(__file__).resolve().parent.parent
    required_dirs = [
        "code", "tests", "data", "data/raw", "data/processed", 
        "data/final", "data/logs", "docs"
    ]
    for d in required_dirs:
        full_path = base_path / d
        assert full_path.exists(), f"Directory {d} does not exist"
        assert full_path.is_dir(), f"{d} is not a directory"

def test_setup_log_exists():
    """Verify that the setup log file exists."""
    base_path = Path(__file__).resolve().parent.parent
    log_path = base_path / "data" / "setup_log.json"
    assert log_path.exists(), "setup_log.json does not exist"

def test_setup_log_schema():
    """Verify the schema of the setup log file."""
    base_path = Path(__file__).resolve().parent.parent
    log_path = base_path / "data" / "setup_log.json"
    
    with open(log_path, "r") as f:
        log_data = json.load(f)
    
    assert "status" in log_data, "Missing 'status' field"
    assert "timestamp" in log_data, "Missing 'timestamp' field"
    assert "paths_verified" in log_data, "Missing 'paths_verified' field"
    assert log_data["status"] in ["SUCCESS", "FAILED"], "Invalid status value"
    assert isinstance(log_data["paths_verified"], list), "paths_verified must be a list"

def test_setup_log_success():
    """Verify that the setup was successful."""
    base_path = Path(__file__).resolve().parent.parent
    log_path = base_path / "data" / "setup_log.json"
    
    with open(log_path, "r") as f:
        log_data = json.load(f)
    
    assert log_data["status"] == "SUCCESS", f"Setup failed: {log_data}"