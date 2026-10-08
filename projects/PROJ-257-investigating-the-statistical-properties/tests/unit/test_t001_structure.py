import json
import os
import pathlib
import pytest

def test_manifest_exists_and_valid():
    """Verify project_structure_manifest.json exists and contains valid data."""
    root = pathlib.Path.cwd()
    manifest_path = root / 'project_structure_manifest.json'
    assert manifest_path.exists(), "project_structure_manifest.json does not exist"
    
    with open(manifest_path, 'r') as f:
        data = json.load(f)
    
    assert isinstance(data, dict), "Manifest must be a dictionary"
    assert len(data) > 0, "Manifest must not be empty"
    
    # Verify required directories are present
    required_dirs = ['src', 'tests', 'data', 'output', 'logs']
    for d in required_dirs:
        found = any(key.startswith(d) for key in data.keys())
        assert found, f"Required directory '{d}' not found in manifest"

def test_directory_structure_created():
    """Verify that the actual directories exist on disk."""
    root = pathlib.Path.cwd()
    required_dirs = [
        'src', 'tests', 'data/raw', 'data/processed', 'data/results',
        'output/results', 'output/figures', 'logs',
        'src/data', 'src/analysis', 'src/viz', 'src/utils',
        'tests/unit', 'tests/integration', 'tests/contract'
    ]
    
    for d in required_dirs:
        dir_path = root / d
        assert dir_path.exists(), f"Directory {d} does not exist"
        assert dir_path.is_dir(), f"{d} is not a directory"
