import json
import os
import pytest
from pathlib import Path

def test_project_structure_manifest_exists():
    """Verify that project_structure_manifest.json exists at the project root."""
    base_dir = Path.cwd()
    manifest_path = base_dir / "project_structure_manifest.json"
    assert manifest_path.exists(), "project_structure_manifest.json not found"

def test_manifest_schema():
    """Verify the manifest JSON schema is correct."""
    base_dir = Path.cwd()
    manifest_path = base_dir / "project_structure_manifest.json"
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    # Check that all keys are absolute paths starting with /
    for key in manifest.keys():
        assert isinstance(key, str), f"Key {key} is not a string"
        assert key.startswith('/'), f"Key {key} does not start with /"
    
    # Check that all values are lists
    for value in manifest.values():
        assert isinstance(value, list), f"Value {value} is not a list"

def test_required_directories_exist():
    """Verify all required directories exist in the manifest."""
    base_dir = Path.cwd()
    manifest_path = base_dir / "project_structure_manifest.json"
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    
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
        "tests/contract"
    ]
    
    # Convert relative paths to absolute for matching
    for rel_dir in required_dirs:
        full_path = str((base_dir / rel_dir).resolve())
        assert full_path in manifest, f"Required directory {rel_dir} not found in manifest"

def test_manifest_is_valid_json():
    """Verify the manifest file is valid JSON."""
    base_dir = Path.cwd()
    manifest_path = base_dir / "project_structure_manifest.json"
    
    try:
        with open(manifest_path) as f:
            json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"Manifest file is not valid JSON: {e}")