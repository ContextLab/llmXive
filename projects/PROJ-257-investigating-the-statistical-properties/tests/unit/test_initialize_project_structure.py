import json
import os
from pathlib import Path
import pytest


class TestInitializeProjectStructure:
    """Unit tests for project directory initialization."""
    
    def test_manifest_exists(self):
        """Verify that project_structure_manifest.json is created."""
        root = Path.cwd()
        manifest_path = root / "project_structure_manifest.json"
        assert manifest_path.exists(), "project_structure_manifest.json must exist"
    
    def test_manifest_valid_json(self):
        """Verify manifest is valid JSON."""
        root = Path.cwd()
        manifest_path = root / "project_structure_manifest.json"
        
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        
        assert isinstance(manifest, dict), "Manifest must be a dictionary"
    
    def test_manifest_has_src_directory(self):
        """Verify manifest contains src directory entry."""
        root = Path.cwd()
        manifest_path = root / "project_structure_manifest.json"
        
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        
        assert len(manifest) > 0, "Manifest must not be empty"
        assert any("src" in key for key in manifest.keys()), "Manifest must contain src directory"
    
    def test_required_directories_exist(self):
        """Verify all required directories are created."""
        root = Path.cwd()
        
        required_dirs = [
            "src",
            "tests",
            "data/raw",
            "data/processed",
            "data/results",
            "output/results",
            "output/figures",
            "logs",
            "src/data",
            "src/analysis",
            "src/viz",
            "src/utils",
            "tests/unit",
            "tests/integration",
            "tests/contract",
        ]
        
        for dir_path in required_dirs:
            full_path = root / dir_path
            assert full_path.exists(), f"Required directory {dir_path} must exist"
            assert full_path.is_dir(), f"{dir_path} must be a directory"
    
    def test_manifest_structure(self):
        """Verify manifest entries have correct structure."""
        root = Path.cwd()
        manifest_path = root / "project_structure_manifest.json"
        
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        
        for path, entry in manifest.items():
            assert "type" in entry, f"Entry for {path} must have 'type' field"
            assert "absolute" in entry, f"Entry for {path} must have 'absolute' field"
            assert entry["type"] == "directory", f"Entry for {path} must be of type 'directory'"
            assert isinstance(entry["absolute"], str), "absolute path must be a string"