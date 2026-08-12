import pytest
from pathlib import Path
import sys
import os
import json
from src.utils.config import get_path


class TestDirectoryStructure:
    """
    Unit tests for T001: Verify project structure creation and manifest generation.
    """

    def test_required_directories_exist(self):
        """Verify that all required directories from T001 exist."""
        project_root = get_path()
        
        required_dirs = [
            "src",
            "src/data",
            "src/synthesis",
            "src/analysis",
            "src/viz",
            "src/utils",
            "tests/unit",
            "tests/integration",
            "tests/contract",
            "data/raw",
            "data/processed",
            "data/results",
            "specs",
            "state"
        ]

        for dir_name in required_dirs:
            full_path = project_root / dir_name
            assert full_path.exists(), f"Required directory missing: {full_path}"
            assert full_path.is_dir(), f"Path exists but is not a directory: {full_path}"

    def test_structure_manifest_exists_and_valid(self):
        """Verify that state/structure_manifest.json exists and contains correct data."""
        project_root = get_path()
        manifest_path = project_root / "state" / "structure_manifest.json"
        
        assert manifest_path.exists(), "state/structure_manifest.json does not exist"
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        # Verify required keys
        assert "created_at" in manifest, "Missing 'created_at' in manifest"
        assert "task_id" in manifest, "Missing 'task_id' in manifest"
        assert manifest["task_id"] == "T001", f"Expected task_id T001, got {manifest['task_id']}"
        assert "created_directories" in manifest, "Missing 'created_directories' in manifest"
        assert manifest["status"] == "success", f"Expected status 'success', got {manifest['status']}"
        
        # Verify all required directories are listed
        required_dirs = [
            "src",
            "src/data",
            "src/synthesis",
            "src/analysis",
            "src/viz",
            "src/utils",
            "tests/unit",
            "tests/integration",
            "tests/contract",
            "data/raw",
            "data/processed",
            "data/results",
            "specs",
            "state"
        ]
        
        for dir_name in required_dirs:
            assert dir_name in manifest["created_directories"], f"Missing directory in manifest: {dir_name}"

    def test_directory_setup_script_exists(self):
        """Verify that the setup script exists."""
        project_root = get_path()
        script_path = project_root / "scripts" / "setup_project_structure.py"
        
        assert script_path.exists(), "scripts/setup_project_structure.py does not exist"