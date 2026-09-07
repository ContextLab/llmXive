import os
import yaml
import tempfile
import shutil
from pathlib import Path
import pytest

from code.utils.update_state_registry import (
    compute_sha256,
    collect_all_artifact_hashes,
    update_state_registry
)

@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    base = tempfile.mkdtemp()
    data_root = Path(base) / "data"
    data_raw = data_root / "raw"
    state_dir = Path(base) / "state" / "projects"
    
    data_raw.mkdir(parents=True)
    state_dir.mkdir(parents=True)

    # Create dummy files
    (data_raw / "workflow_1.json").write_text('{"id": 1}')
    (data_raw / "workflow_2.json").write_text('{"id": 2}')
    
    state_file = state_dir / "test_project.yaml"
    state_file.touch()

    yield {
        "base": base,
        "data_root": data_root,
        "state_file": state_file,
        "project_id": "test_project"
    }

    shutil.rmtree(base)

def test_compute_sha256(temp_dirs):
    """Test SHA-256 computation for a known file."""
    file_path = temp_dirs["data_root"] / "raw" / "workflow_1.json"
    hash_val = compute_sha256(file_path)
    assert isinstance(hash_val, str)
    assert len(hash_val) == 64  # SHA-256 hex length

def test_collect_all_artifact_hashes(temp_dirs):
    """Test collection of hashes from data directory."""
    hashes = collect_all_artifact_hashes(temp_dirs["data_root"])
    
    assert "raw/workflow_1.json" in hashes
    assert "raw/workflow_2.json" in hashes
    assert len(hashes) == 2

def test_update_state_registry(temp_dirs):
    """Test updating the state registry with artifact hashes."""
    state_file = temp_dirs["state_file"]
    data_root = temp_dirs["data_root"]
    project_id = temp_dirs["project_id"]

    # Perform update
    updated_state = update_state_registry(state_file, data_root, project_id)

    # Verify structure
    assert "projects" in updated_state
    assert project_id in updated_state["projects"]
    assert "artifact_hashes" in updated_state["projects"][project_id]
    assert "updated_at" in updated_state["projects"][project_id]

    # Verify content
    hashes = updated_state["projects"][project_id]["artifact_hashes"]
    assert "raw/workflow_1.json" in hashes
    assert "raw/workflow_2.json" in hashes

    # Verify file on disk
    with open(state_file, "r") as f:
        disk_state = yaml.safe_load(f)
    
    assert disk_state == updated_state

def test_update_state_registry_missing_data_root(temp_dirs):
    """Test behavior when data root does not exist."""
    non_existent = Path(temp_dirs["base"]) / "non_existent"
    state_file = temp_dirs["state_file"]
    project_id = temp_dirs["project_id"]

    # Should return empty hashes without raising error if dir missing (handled in logic)
    # But our implementation checks existence before walking. 
    # Let's verify the function handles it gracefully or raises.
    # Based on implementation: if not data_root.exists(): return artifacts (empty dict)
    # But the main() checks existence. Let's test the function directly.
    
    updated_state = update_state_registry(state_file, non_existent, project_id)
    assert updated_state["projects"][project_id]["artifact_hashes"] == {}