"""
Unit tests for T001: Project Structure Creation.
Verifies that the required directories and manifest file exist.
"""
import os
import json
import pytest
from pathlib import Path
import sys

# Add parent directory to path to import setup_structure if needed, 
# though we are mostly testing file system state.
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

class TestProjectStructure:
    """Tests for the project structure created by T001."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).resolve().parent.parent.parent

    def test_root_directories_exist(self, project_root):
        """Verify top-level directories exist."""
        required_dirs = ["code", "data", "state", "tests", "docs", "specs"]
        for dir_name in required_dirs:
            dir_path = project_root / dir_name
            assert dir_path.exists(), f"Directory {dir_name} does not exist"
            assert dir_path.is_dir(), f"{dir_name} is not a directory"

    def test_data_subdirectories_exist(self, project_root):
        """Verify data subdirectories exist."""
        required_dirs = [
            "data/raw", "data/processed", "data/results", 
            "data/config", "data/quality", "data/processed/connectivity_matrices"
        ]
        for dir_path_str in required_dirs:
            dir_path = project_root / dir_path_str
            assert dir_path.exists(), f"Directory {dir_path_str} does not exist"

    def test_tests_subdirectories_exist(self, project_root):
        """Verify test subdirectories exist."""
        required_dirs = ["tests/unit", "tests/integration", "tests/benchmark"]
        for dir_path_str in required_dirs:
            dir_path = project_root / dir_path_str
            assert dir_path.exists(), f"Directory {dir_path_str} does not exist"

    def test_docs_subdirectories_exist(self, project_root):
        """Verify docs subdirectories exist."""
        required_dirs = ["docs/decisions"]
        for dir_path_str in required_dirs:
            dir_path = project_root / dir_path_str
            assert dir_path.exists(), f"Directory {dir_path_str} does not exist"

    def test_structure_manifest_exists(self, project_root):
        """Verify the structure manifest file exists and is valid JSON."""
        manifest_path = project_root / "state" / "structure_manifest.json"
        assert manifest_path.exists(), "structure_manifest.json does not exist"
        
        with open(manifest_path, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                pytest.fail("structure_manifest.json is not valid JSON")

        assert "task_id" in data, "Manifest missing 'task_id'"
        assert data["task_id"] == "T001", "Manifest task_id is not T001"
        assert "created_at" in data, "Manifest missing 'created_at'"
        assert "directories" in data, "Manifest missing 'directories'"