"""
Unit tests for download_moral_machine.py
"""
import os
import sys
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from download_moral_machine import (
    compute_sha256,
    ensure_directories,
    ensure_state_file,
    update_state_checksum
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_compute_sha256(temp_dir):
    """Test SHA-256 computation."""
    test_file = temp_dir / "test.txt"
    test_content = b"Hello, World!"
    test_file.write_bytes(test_content)
    
    checksum = compute_sha256(test_file)
    expected = hashlib.sha256(test_content).hexdigest()
    
    assert checksum == expected

def test_ensure_directories(temp_dir):
    """Test directory creation."""
    # Mock the constants to use temp_dir
    import download_moral_machine as module
    
    original_data_dir = module.DATA_DIR
    original_state_dir = module.STATE_DIR
    original_project_root = module.PROJECT_ROOT
    
    try:
        module.DATA_DIR = temp_dir / "data" / "raw"
        module.STATE_DIR = temp_dir / "state" / "projects"
        module.PROJECT_ROOT = temp_dir
        
        ensure_directories()
        
        assert module.DATA_DIR.exists()
        assert module.STATE_DIR.exists()
    finally:
        # Restore original values
        module.DATA_DIR = original_data_dir
        module.STATE_DIR = original_state_dir
        module.PROJECT_ROOT = original_project_root

def test_ensure_state_file(temp_dir):
    """Test state file creation."""
    import download_moral_machine as module
    
    original_state_dir = module.STATE_DIR
    original_state_file = module.STATE_FILE
    
    try:
        module.STATE_DIR = temp_dir / "state" / "projects"
        module.STATE_FILE = module.STATE_DIR / "test_state.yaml"
        
        ensure_state_file()
        
        assert module.STATE_FILE.exists()
        
        with open(module.STATE_FILE, 'r') as f:
            data = yaml.safe_load(f)
        
        assert "project_id" in data
        assert "artifact_hashes" in data
    finally:
        module.STATE_DIR = original_state_dir
        module.STATE_FILE = original_state_file

def test_update_state_checksum(temp_dir):
    """Test state file checksum update."""
    import download_moral_machine as module
    
    original_state_file = module.STATE_FILE
    
    try:
        module.STATE_FILE = temp_dir / "test_state.yaml"
        
        # Create initial state file
        ensure_state_file()
        
        test_checksum = "abc123"
        update_state_checksum(test_checksum)
        
        with open(module.STATE_FILE, 'r') as f:
            data = yaml.safe_load(f)
        
        assert data["artifact_hashes"]["moral_machine_dataset"] == test_checksum
        assert "updated_at" in data
    finally:
        module.STATE_FILE = original_state_file
