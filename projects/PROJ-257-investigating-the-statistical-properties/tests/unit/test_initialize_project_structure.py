import json
import os
import tempfile
from pathlib import Path
import pytest

from initialize_project_structure import create_directories, generate_manifest, main

class TestInitializeProjectStructure:
    """Unit tests for T001 project structure initialization."""

    def test_create_directories_creates_all_required_paths(self, tmp_path):
        """Test that all required directories are created."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            created = create_directories()
            
            required_dirs = [
                "src", "tests", "data/raw", "data/processed", "data/results",
                "output/results", "output/figures", "logs",
                "src/data", "src/analysis", "src/viz", "src/utils",
                "tests/unit", "tests/integration", "tests/contract"
            ]
            
            for dir_name in required_dirs:
                expected_path = tmp_path / dir_name
                assert expected_path.exists(), f"Directory {dir_name} was not created"
                assert expected_path.is_dir(), f"{dir_name} is not a directory"
        finally:
            os.chdir(original_cwd)

    def test_generate_manifest_creates_valid_json(self, tmp_path):
        """Test that the manifest file is created and contains valid JSON."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            create_directories()
            manifest_path = generate_manifest()
            
            assert manifest_path.exists(), "Manifest file was not created"
            
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            assert isinstance(manifest, dict), "Manifest must be a dictionary"
        finally:
            os.chdir(original_cwd)

    def test_manifest_keys_are_absolute_paths(self, tmp_path):
        """Test that all keys in the manifest are absolute path strings starting with '/'."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            create_directories()
            manifest_path = generate_manifest()
            
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            for key in manifest.keys():
                assert isinstance(key, str), f"Key {key} is not a string"
                assert key.startswith('/'), f"Key {key} does not start with '/'"
        finally:
            os.chdir(original_cwd)

    def test_manifest_values_are_lists(self, tmp_path):
        """Test that all values in the manifest are lists."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            create_directories()
            manifest_path = generate_manifest()
            
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            for value in manifest.values():
                assert isinstance(value, list), f"Value {value} is not a list"
        finally:
            os.chdir(original_cwd)

    def test_main_execution_succeeds(self, tmp_path):
        """Test that the main function executes successfully."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = main()
            assert result == 0, "main() did not return 0"
            assert (tmp_path / "project_structure_manifest.json").exists(), "Manifest not created by main()"
        finally:
            os.chdir(original_cwd)

    def test_verification_command_compatibility(self, tmp_path):
        """
        Test that the generated manifest passes the exact verification command
        specified in T001:
        python -c "import json, os; m=json.load(open(os.path.abspath('project_structure_manifest.json'))); assert all(isinstance(v, list) for v in m.values()); assert all(isinstance(k, str) and k.startswith('/') for k in m.keys())"
        """
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            create_directories()
            generate_manifest()
            
            # Simulate the verification command
            import subprocess
            cmd = [
                "python", "-c",
                "import json, os; "
                "m=json.load(open(os.path.abspath('project_structure_manifest.json'))); "
                "assert all(isinstance(v, list) for v in m.values()); "
                "assert all(isinstance(k, str) and k.startswith('/') for k in m.keys())"
            ]
            
            result = subprocess.run(cmd, cwd=tmp_path, capture_output=True, text=True)
            assert result.returncode == 0, f"Verification command failed: {result.stderr}"
        finally:
            os.chdir(original_cwd)
