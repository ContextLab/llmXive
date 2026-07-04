import json
import os
import tempfile
import shutil
from pathlib import Path
import pytest

import sys
# Add the code directory to the path to allow imports
code_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(code_dir))

from src.utils.manifest_manager import (
    compute_file_hash,
    load_manifest,
    save_manifest,
    initialize_manifest,
    register_artifact,
    verify_artifact,
    MANIFEST_PATH
)

@pytest.fixture
def temp_project_root():
    """Create a temporary directory structure for testing."""
    temp_dir = tempfile.mkdtemp()
    # Create a mock project structure
    state_dir = Path(temp_dir) / "state"
    state_dir.mkdir()
    data_dir = Path(temp_dir) / "data"
    data_dir.mkdir()
    
    # Mock a test file
    test_file = data_dir / "test.txt"
    test_file.write_text("test content")

    # Temporarily override the global MANIFEST_PATH logic by mocking the module
    # Since MANIFEST_PATH is defined at module level, we need to patch the module behavior
    # or re-implement the logic in the test. 
    # To keep it simple and robust, we will patch the MANIFEST_PATH variable in the module.
    import src.utils.manifest_manager as mm
    original_path = mm.MANIFEST_PATH
    mm.MANIFEST_PATH = state_dir / "manifest.json"
    mm.PROJECT_ROOT = Path(temp_dir)

    yield temp_dir, state_dir, data_dir, test_file

    # Restore original path
    mm.MANIFEST_PATH = original_path
    mm.PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    shutil.rmtree(temp_dir)

def test_compute_file_hash(temp_project_root):
    _, _, _, test_file = temp_project_root
    hash_val = compute_file_hash(str(test_file))
    assert len(hash_val) == 64  # SHA-256 hex length
    assert isinstance(hash_val, str)

def test_initialize_manifest(temp_project_root):
    state_dir = temp_project_root[1]
    manifest_path = state_dir / "manifest.json"
    
    assert not manifest_path.exists()
    initialize_manifest()
    assert manifest_path.exists()
    
    manifest = load_manifest()
    assert manifest["version"] == "1.0"
    assert manifest["artifacts"] == {}

def test_load_manifest_when_empty(temp_project_root):
    state_dir = temp_project_root[1]
    manifest_path = state_dir / "manifest.json"
    # Ensure it doesn't exist
    if manifest_path.exists():
        manifest_path.unlink()
        
    manifest = load_manifest()
    assert manifest["version"] == "1.0"
    assert manifest["artifacts"] == {}

def test_register_artifact(temp_project_root):
    _, _, data_dir, test_file = temp_project_root
    
    # Register the test file
    success = register_artifact(
        str(test_file), 
        "test_type", 
        "Test description"
    )
    assert success is True
    
    manifest = load_manifest()
    # The path stored should be relative to PROJECT_ROOT
    relative_path = str(test_file.relative_to(Path(temp_project_root[0])))
    
    assert relative_path in manifest["artifacts"]
    assert manifest["artifacts"][relative_path]["type"] == "test_type"
    assert "hash" in manifest["artifacts"][relative_path]

def test_verify_artifact_success(temp_project_root):
    _, _, data_dir, test_file = temp_project_root
    register_artifact(str(test_file), "test_type")
    
    assert verify_artifact(str(test_file)) is True

def test_verify_artifact_failure_modified(temp_project_root):
    _, _, data_dir, test_file = temp_project_root
    register_artifact(str(test_file), "test_type")
    
    # Modify the file
    test_file.write_text("modified content")
    
    assert verify_artifact(str(test_file)) is False

def test_verify_artifact_failure_missing(temp_project_root):
    _, _, data_dir, test_file = temp_project_root
    register_artifact(str(test_file), "test_type")
    
    # Delete the file
    test_file.unlink()
    
    assert verify_artifact(str(test_file)) is False

def test_save_and_load_manifest(temp_project_root):
    state_dir = temp_project_root[1]
    manifest_path = state_dir / "manifest.json"
    
    test_data = {"key": "value", "count": 10}
    save_manifest(test_data)
    
    loaded = load_manifest()
    assert loaded == test_data
    assert manifest_path.exists()
