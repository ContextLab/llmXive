"""
Unit tests for T001: Verify project structure creation.

These tests validate that the required directories exist
and that the manifest file was created correctly.
"""
import os
import json
import pytest
from pathlib import Path

REQUIRED_DIRS = ["code", "data", "state", "tests", "docs"]
MANIFEST_PATH = Path("docs") / "structure_manifest.json"

class TestT001Structure:
    """Tests for project structure validation."""

    def test_required_directories_exist(self):
        """Verify all required directories exist."""
        for dir_name in REQUIRED_DIRS:
            dir_path = Path(dir_name)
            assert dir_path.exists(), f"Directory {dir_name} does not exist"
            assert dir_path.is_dir(), f"{dir_name} is not a directory"

    def test_manifest_file_exists(self):
        """Verify the structure manifest file exists."""
        assert MANIFEST_PATH.exists(), "Structure manifest not found"
        assert MANIFEST_PATH.is_file(), "Manifest is not a file"

    def test_manifest_is_valid_json(self):
        """Verify the manifest contains valid JSON."""
        with open(MANIFEST_PATH, 'r') as f:
            data = json.load(f)
        assert isinstance(data, dict), "Manifest content is not a JSON object"

    def test_manifest_contains_required_fields(self):
        """Verify the manifest contains expected metadata fields."""
        with open(MANIFEST_PATH, 'r') as f:
            data = json.load(f)
        
        required_keys = ["task_id", "description", "created_at", "directories", "status"]
        for key in required_keys:
            assert key in data, f"Missing required key in manifest: {key}"

    def test_manifest_task_id_is_t001(self):
        """Verify the manifest identifies this as T001."""
        with open(MANIFEST_PATH, 'r') as f:
            data = json.load(f)
        assert data["task_id"] == "T001", "Manifest task_id is not T001"

    def test_manifest_lists_all_directories(self):
        """Verify the manifest lists all required directories."""
        with open(MANIFEST_PATH, 'r') as f:
            data = json.load(f)
        
        dirs_in_manifest = data.get("directories", [])
        for dir_name in REQUIRED_DIRS:
            # Check if the directory name appears in the path list
            found = any(dir_name in path for path in dirs_in_manifest)
            assert found, f"Directory {dir_name} not found in manifest"

    def test_directories_are_writable(self):
        """Verify we can write a temporary file to each directory."""
        for dir_name in REQUIRED_DIRS:
            dir_path = Path(dir_name)
            temp_file = dir_path / ".test_writable"
            try:
                temp_file.touch()
                temp_file.unlink()
            except (OSError, IOError) as e:
                pytest.fail(f"Cannot write to directory {dir_name}: {e}")