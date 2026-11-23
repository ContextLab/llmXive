import os
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import yaml

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.utils import state_manager

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_file(temp_dir):
    file_path = temp_dir / "test.txt"
    file_path.write_text("test content")
    return file_path

def test_compute_file_hash(sample_file):
    expected = hashlib.sha256(b"test content").hexdigest()
    result = state_manager.compute_file_hash(sample_file)
    assert result == expected

def test_compute_file_hash_missing(temp_dir):
    missing_file = temp_dir / "nonexistent.txt"
    with pytest.raises(FileNotFoundError):
        state_manager.compute_file_hash(missing_file)

def test_scan_directory_for_artifacts(temp_dir):
    # Create some files
    (temp_dir / "sub").mkdir()
    (temp_dir / "file1.txt").write_text("a")
    (temp_dir / "sub" / "file2.txt").write_text("b")

    files = state_manager.scan_directory_for_artifacts(temp_dir)
    assert len(files) == 2
    assert all(f.is_file() for f in files)

def test_scan_directory_nonexistent(temp_dir):
    non_existent = temp_dir / "does_not_exist"
    files = state_manager.scan_directory_for_artifacts(non_existent)
    assert files == []

def test_load_state_missing_file(temp_dir, monkeypatch):
    # Mock the state file path
    mock_state_file = temp_dir / "missing.yaml"
    monkeypatch.setattr(state_manager, "STATE_FILE", mock_state_file)

    state = state_manager.load_state()
    assert "project_id" in state
    assert "artifact_hashes" in state

def test_save_state_and_load(temp_dir, monkeypatch):
    mock_state_file = temp_dir / "state.yaml"
    monkeypatch.setattr(state_manager, "STATE_FILE", mock_state_file)

    test_state = {"key": "value", "nested": {"a": 1}}
    state_manager.save_state(test_state)

    assert mock_state_file.exists()
    loaded = state_manager.load_state()
    assert loaded == test_state

def test_update_artifact_hashes_integration(temp_dir, monkeypatch, caplog):
    # Setup temp directories
    data_raw = temp_dir / "data" / "raw"
    data_processed = temp_dir / "data" / "processed"
    data_raw.mkdir(parents=True)
    data_processed.mkdir(parents=True)

    # Create a dummy file
    dummy = data_raw / "dummy.txt"
    dummy.write_text("content")

    # Mock paths
    monkeypatch.setattr(state_manager, "PROJECT_ROOT", temp_dir)
    monkeypatch.setattr(state_manager, "STATE_FILE", temp_dir / "state.yaml")
    monkeypatch.setattr(state_manager, "DATA_RAW_DIR", data_raw)
    monkeypatch.setattr(state_manager, "DATA_PROCESSED_DIR", data_processed)

    state_manager.update_artifact_hashes()

    state = state_manager.load_state()
    assert "data/raw" in state["artifact_hashes"]
    assert "dummy.txt" in state["artifact_hashes"]["data/raw"]
    assert state["artifact_hashes"]["data/raw"]["dummy.txt"] == hashlib.sha256(b"content").hexdigest()

def test_verify_artifacts(temp_dir, monkeypatch):
    # Setup
    data_raw = temp_dir / "data" / "raw"
    data_raw.mkdir(parents=True)
    dummy = data_raw / "dummy.txt"
    dummy.write_text("content")

    # Mock paths
    monkeypatch.setattr(state_manager, "PROJECT_ROOT", temp_dir)
    monkeypatch.setattr(state_manager, "STATE_FILE", temp_dir / "state.yaml")
    monkeypatch.setattr(state_manager, "DATA_RAW_DIR", data_raw)
    monkeypatch.setattr(state_manager, "DATA_PROCESSED_DIR", temp_dir / "data" / "processed")

    # Save correct state
    correct_state = {
        "artifact_hashes": {
            "data/raw": {"dummy.txt": hashlib.sha256(b"content").hexdigest()},
            "data/processed": {}
        }
    }
    state_manager.save_state(correct_state)

    # Verify
    assert state_manager.verify_artifacts() is True

    # Corrupt file content
    dummy.write_text("changed")
    assert state_manager.verify_artifacts() is False
