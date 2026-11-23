"""
Tests for the hash_artifacts module.
"""

import os
import tempfile
import yaml
from pathlib import Path
import pytest

from hash_artifacts import (
    calculate_sha256,
    get_artifact_files,
    generate_artifact_hashes,
    load_state,
    save_state,
    update_state_with_hashes,
    main,
)


def test_calculate_sha256(tmp_path):
    """Test SHA-256 calculation on a known string."""
    test_file = tmp_path / "test.txt"
    content = b"Hello, World!"
    test_file.write_bytes(content)

    hash_val = calculate_sha256(test_file)
    # Known SHA-256 for "Hello, World!"
    expected = "d9014c4624844aa5bac314773d6b689ad467fa4e1d1a50a1b8a99d5a95f72ff5"
    assert hash_val == expected


def test_calculate_sha256_empty_file(tmp_path):
    """Test SHA-256 on an empty file."""
    test_file = tmp_path / "empty.txt"
    test_file.write_bytes(b"")

    hash_val = calculate_sha256(test_file)
    # Known SHA-256 for empty string
    expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert hash_val == expected


def test_get_artifact_files(tmp_path):
    """Test recursive file retrieval."""
    # Create nested structure
    (tmp_path / "subdir").mkdir()
    (tmp_path / "file1.txt").write_text("a")
    (tmp_path / "subdir" / "file2.txt").write_text("b")

    files = get_artifact_files(tmp_path)
    assert len(files) == 2
    # Check that both files are found (order might vary, but we sort in func)
    names = [f.name for f in files]
    assert "file1.txt" in names
    assert "file2.txt" in names


def test_get_artifact_files_empty_dir(tmp_path):
    """Test file retrieval on empty directory."""
    files = get_artifact_files(tmp_path)
    assert files == []


def test_generate_artifact_hashes(tmp_path):
    """Test hash generation for multiple files."""
    (tmp_path / "file1.txt").write_text("content1")
    (tmp_path / "file2.txt").write_text("content2")

    hashes = generate_artifact_hashes(tmp_path)
    
    assert len(hashes) == 2
    assert "file1.txt" in hashes
    assert "file2.txt" in hashes
    assert hashes["file1.txt"] != hashes["file2.txt"]


def test_load_state_existing(tmp_path):
    """Test loading an existing state file."""
    state_file = tmp_path / "state.yaml"
    expected_state = {"key": "value", "nested": {"a": 1}}
    with open(state_file, "w") as f:
        yaml.dump(expected_state, f)

    loaded = load_state(state_file)
    assert loaded == expected_state


def test_load_state_missing(tmp_path):
    """Test loading a missing state file."""
    state_file = tmp_path / "nonexistent.yaml"
    loaded = load_state(state_file)
    assert loaded == {}


def test_save_state(tmp_path):
    """Test saving state to a file."""
    state_file = tmp_path / "state.yaml"
    test_state = {"new_key": 123}

    save_state(state_file, test_state)

    assert state_file.exists()
    with open(state_file, "r") as f:
        loaded = yaml.safe_load(f)
    assert loaded == test_state


def test_update_state_with_hashes():
    """Test updating state with new hashes."""
    initial_state = {"other": "data"}
    new_hashes = {"file1.txt": "abc123", "file2.txt": "def456"}

    updated = update_state_with_hashes(initial_state, new_hashes)

    assert "artifacts" in updated
    assert "hashes" in updated["artifacts"]
    assert "last_updated" in updated["artifacts"]
    assert updated["artifacts"]["hashes"] == new_hashes
    assert updated["other"] == "data"  # Preserve existing data


def test_update_state_empty_initial():
    """Test updating state when initial state is empty."""
    initial_state = {}
    new_hashes = {"file1.txt": "abc123"}

    updated = update_state_with_hashes(initial_state, new_hashes)

    assert "artifacts" in updated
    assert updated["artifacts"]["hashes"] == new_hashes


def test_main_no_artifacts_dir(capsys):
    """Test main function when artifacts dir does not exist."""
    # Create a temp dir to act as project root
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_root = Path(tmp_dir)
        artifacts_dir = project_root / "artifacts"
        state_dir = project_root / "state"
        state_file = state_dir / "project_state.yaml"

        # Change to temp dir so Path.cwd() works
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            # Ensure artifacts dir does NOT exist
            assert not artifacts_dir.exists()
            
            result = main()
            
            assert result == 0
            assert state_file.exists()
            
            with open(state_file, "r") as f:
                state = yaml.safe_load(f)
            
            assert "artifacts" in state
            assert state["artifacts"]["hashes"] == {}
        finally:
            os.chdir(old_cwd)


def test_main_with_artifacts(tmp_path, capsys):
    """Test main function when artifacts dir exists with files."""
    # Setup
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()
    (artifacts_dir / "test_artifact.txt").write_text("test content")
    
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    state_file = state_dir / "project_state.yaml"
    
    # Pre-populate state
    with open(state_file, "w") as f:
        yaml.dump({"existing": "data"}, f)

    # Change to tmp_path
    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = main()
        
        assert result == 0
        assert state_file.exists()
        
        with open(state_file, "r") as f:
            state = yaml.safe_load(f)
        
        assert "artifacts" in state
        assert "hashes" in state["artifacts"]
        assert "test_artifact.txt" in state["artifacts"]["hashes"]
        assert state["existing"] == "data"  # Existing data preserved
    finally:
        os.chdir(old_cwd)
