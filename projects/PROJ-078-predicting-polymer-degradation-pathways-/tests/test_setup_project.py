"""
Tests for the setup_project module.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the module under test
from setup_project import create_directories, verify_directories, generate_setup_log

@pytest.fixture
def temp_base_path():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_create_directories_creates_all_needed(temp_base_path):
    """Test that create_directories creates all required subdirectories."""
    expected_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/reports",
        "tests",
        "state",
        "state/projects"
    ]
    
    created = create_directories(temp_base_path)
    
    assert len(created) == len(expected_dirs)
    
    for dir_name in expected_dirs:
        full_path = temp_base_path / dir_name
        assert full_path.is_dir(), f"Directory {full_path} was not created"

def test_create_directories_idempotent(temp_base_path):
    """Test that creating directories twice does not raise errors."""
    create_directories(temp_base_path)
    # Running again should not raise an exception
    created_again = create_directories(temp_base_path)
    assert len(created_again) == 7

def test_verify_directories_returns_true_when_all_exist(temp_base_path):
    """Test that verify_directories returns True when all dirs exist."""
    create_directories(temp_base_path)
    assert verify_directories(temp_base_path) is True

def test_verify_directories_returns_false_when_missing(temp_base_path):
    """Test that verify_directories returns False when a dir is missing."""
    # Create some but not all directories
    (temp_base_path / "code").mkdir()
    (temp_base_path / "tests").mkdir()
    
    assert verify_directories(temp_base_path) is False

def test_generate_setup_log_creates_file(temp_base_path):
    """Test that generate_setup_log creates the log file."""
    create_directories(temp_base_path)
    log_path = generate_setup_log(temp_base_path)
    
    assert log_path.exists()
    assert log_path.name == "setup_log.txt"
    
    # Check content
    with open(log_path, 'r') as f:
        content = f.read()
    
    assert "Project Setup Log" in content
    assert "Generated:" in content
    assert "code/" in content
    assert "data/raw/" in content
