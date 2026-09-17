import os
import json
import pytest
from pathlib import Path
import sys

# Add code to path if running from root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.setup_project_structure import create_directories, generate_tree_manifest

def test_directory_creation(tmp_path):
    """Test that the required directory structure is created."""
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        
        # Create directories
        created = create_directories()
        
        # Verify data directories exist
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "simulated").exists()
        assert (tmp_path / "data" / "results").exists()
        
        # Verify code directories exist
        assert (tmp_path / "code" / "simulation").exists()
        assert (tmp_path / "code" / "models").exists()
        assert (tmp_path / "code" / "metrics").exists()
        assert (tmp_path / "code" / "validation").exists()
        assert (tmp_path / "code" / "plots").exists()
        assert (tmp_path / "code" / "scripts").exists()
        
        # Verify test directories exist
        assert (tmp_path / "tests" / "unit").exists()
        assert (tmp_path / "tests" / "integration").exists()
        
        # Verify docs directory exists
        assert (tmp_path / "docs" / "paper").exists()
        
        # Verify .gitkeep files in data directories
        assert (tmp_path / "data" / "raw" / ".gitkeep").exists()
        assert (tmp_path / "data" / "simulated" / ".gitkeep").exists()
        assert (tmp_path / "data" / "results" / ".gitkeep").exists()
        
    finally:
        os.chdir(original_cwd)

def test_tree_manifest_creation(tmp_path):
    """Test that the tree_manifest.json is created and valid."""
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        
        # Create directories
        create_directories()
        
        # Generate manifest
        manifest_path = generate_tree_manifest([str(tmp_path / "data" / "raw")])
        
        assert os.path.exists(manifest_path)
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        assert "created_paths" in manifest
        assert isinstance(manifest["created_paths"], list)
        assert len(manifest["created_paths"]) > 0
        
        # Check that paths are absolute
        for path in manifest["created_paths"]:
            assert os.path.isabs(path)
            
    finally:
        os.chdir(original_cwd)