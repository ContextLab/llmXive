import os
import json
import pytest
from pathlib import Path
from setup_structure import create_directories, create_manifest

def test_directories_exist():
    """
    Verifies that the required project directories exist after creation.
    This is the primary validation for T001.
    """
    required_dirs = [
        "code", "data", "state", "tests", "docs",
        "data/raw", "data/processed", "data/quality", "data/results",
        "code/data", "code/network", "code/stats", "code/viz",
        "tests/unit", "tests/integration", "docs/decisions"
    ]
    
    for d in required_dirs:
        path = Path(d)
        assert path.exists(), f"Directory {d} does not exist"
        assert path.is_dir(), f"Path {d} is not a directory"

def test_manifest_generation(tmp_path):
    """
    Tests that create_manifest generates a valid JSON file.
    """
    # Mock a list of created directories
    test_dirs = ["code", "data", "state"]
    
    # Change to temp directory for safe writing
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        manifest_path = create_manifest(test_dirs)
        
        assert manifest_path.exists(), "Manifest file was not created"
        
        with open(manifest_path, 'r') as f:
            data = json.load(f)
        
        assert "timestamp" in data
        assert data["task_id"] == "T001"
        assert data["status"] == "success"
        assert "directories_created" in data
    finally:
        os.chdir(original_cwd)

def test_structure_snapshot():
    """
    Verifies the specific sub-structures required by the pipeline.
    """
    # Check for connectivity matrices directory
    assert Path("data/processed/connectivity_matrices").exists()
    
    # Check for config directory
    assert Path("data/config").exists()
    
    # Check for decisions directory
    assert Path("docs/decisions").exists()
