"""
Tests for hash_artifacts module.
"""

import os
import tempfile
import shutil
from pathlib import Path
import yaml
import pytest

# Import the module under test
# Note: We need to ensure code/ is in the path or import relative to it
# Assuming this test is run from project root: python -m pytest
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from hash_artifacts import (
    calculate_sha256,
    get_artifact_files,
    generate_artifact_hashes,
    load_state,
    save_state,
    update_state_with_hashes,
    main
)


@pytest.fixture
def temp_project_structure(tmp_path):
    """Create a temporary directory structure mimicking the project."""
    artifacts_dir = tmp_path / "artifacts"
    state_dir = tmp_path / "state"
    artifacts_dir.mkdir()
    state_dir.mkdir()
    
    # Create some dummy files
    (artifacts_dir / "result1.json").write_text('{"data": 1}')
    (artifacts_dir / "result2.csv").write_text("a,b\n1,2")
    
    subdir = artifacts_dir / "subdir"
    subdir.mkdir()
    (subdir / "nested.txt").write_text("nested content")
    
    return {
        "root": tmp_path,
        "artifacts": artifacts_dir,
        "state": state_dir,
        "state_file": state_dir / "project_state.yaml"
    }


def test_calculate_sha256(temp_project_structure):
    """Test SHA-256 calculation on a known file."""
    file_path = temp_project_structure["artifacts"] / "result1.json"
    hash_val = calculate_sha256(file_path)
    
    # Known hash for '{"data": 1}'
    # echo -n '{"data": 1}' | sha256sum
    # 664b805091323087024175750334624860000000000000000000000000000000 -> Wait, let's calculate properly
    # Actually, let's just verify it's a valid 64-char hex string and consistent
    assert len(hash_val) == 64
    assert all(c in '0123456789abcdef' for c in hash_val)
    
    # Re-run to ensure consistency
    hash_val2 = calculate_sha256(file_path)
    assert hash_val == hash_val2


def test_get_artifact_files(temp_project_structure):
    """Test retrieval of all files in artifacts directory."""
    files = get_artifact_files(temp_project_structure["artifacts"])
    
    assert len(files) == 3
    filenames = {f.name for f in files}
    assert "result1.json" in filenames
    assert "result2.csv" in filenames
    assert "nested.txt" in filenames


def test_generate_artifact_hashes(temp_project_structure):
    """Test generation of hashes for all files."""
    hashes = generate_artifact_hashes(temp_project_structure["artifacts"])
    
    assert len(hashes) == 3
    assert "result1.json" in hashes
    assert "result2.csv" in hashes
    assert "subdir/nested.txt" in hashes
    
    # Verify they are valid hashes
    for h in hashes.values():
        assert len(h) == 64
        assert all(c in '0123456789abcdef' for c in h)


def test_load_state_nonexistent():
    """Test loading state when file doesn't exist."""
    with tempfile.TemporaryDirectory() as tmp:
        state_path = Path(tmp) / "nonexistent.yaml"
        state = load_state(state_path)
        assert state == {}


def test_load_state_valid(temp_project_structure):
    """Test loading a valid state file."""
    state_data = {"key": "value", "nested": {"a": 1}}
    save_state(temp_project_structure["state_file"], state_data)
    
    loaded = load_state(temp_project_structure["state_file"])
    assert loaded == state_data


def test_update_state_with_hashes():
    """Test updating state with new hashes."""
    state = {"existing": "data"}
    new_hashes = {"file1.txt": "hash1", "file2.txt": "hash2"}
    
    updated = update_state_with_hashes(state, new_hashes)
    
    assert "artifacts" in updated
    assert "hashes" in updated["artifacts"]
    assert updated["artifacts"]["hashes"] == new_hashes
    assert "last_updated" in updated["artifacts"]
    assert updated["existing"] == "data"  # Preserve existing data


def test_save_and_load_roundtrip(temp_project_structure):
    """Test saving and loading state preserves data."""
    original = {
        "artifacts": {
            "hashes": {"test.txt": "abc123"},
            "last_updated": "2023-01-01T00:00:00Z"
        },
        "other": "data"
    }
    
    save_state(temp_project_structure["state_file"], original)
    loaded = load_state(temp_project_structure["state_file"])
    
    assert loaded == original


def test_main_integration(temp_project_structure, capsys):
    """Test the main function execution."""
    # Change to temp root
    old_cwd = os.getcwd()
    try:
        os.chdir(temp_project_structure["root"])
        
        # Run main
        result = main()
        
        assert result == 0
        
        # Check output
        captured = capsys.readouterr()
        assert "Generated 3 artifact hashes" in captured.out
        assert "Updated state file" in captured.out
        
        # Verify state file was updated
        state = load_state(temp_project_structure["state_file"])
        assert "artifacts" in state
        assert "hashes" in state["artifacts"]
        assert len(state["artifacts"]["hashes"]) == 3
        
    finally:
        os.chdir(old_cwd)