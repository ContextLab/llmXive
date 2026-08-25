import os
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from src.utils import state_manager


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_file(temp_dir):
    file_path = temp_dir / "test.txt"
    file_path.write_text("hello world")
    return file_path


def test_compute_file_hash(sample_file):
    expected_hash = hashlib.sha256(b"hello world").hexdigest()
    result = state_manager.compute_file_hash(sample_file)
    assert result == expected_hash


def test_compute_file_hash_missing(temp_dir):
    missing_file = temp_dir / "nonexistent.txt"
    with pytest.raises(FileNotFoundError):
        state_manager.compute_file_hash(missing_file)


def test_scan_directory_for_artifacts(temp_dir):
    (temp_dir / "subdir").mkdir()
    (temp_dir / "file1.txt").write_text("data1")
    (temp_dir / "subdir" / "file2.txt").write_text("data2")

    artifacts = state_manager.scan_directory_for_artifacts(temp_dir)

    assert "file1.txt" in artifacts
    assert "subdir/file2.txt" in artifacts
    assert len(artifacts) == 2


def test_scan_directory_nonexistent(temp_dir):
    nonexistent = temp_dir / "does_not_exist"
    artifacts = state_manager.scan_directory_for_artifacts(nonexistent)
    assert artifacts == {}


def test_load_state_missing_file(temp_dir):
    missing_path = temp_dir / "missing.yaml"
    state = state_manager.load_state(missing_path)
    assert state == {"projects": {}}


def test_save_state_and_load(temp_dir):
    state_path = temp_dir / "state.yaml"
    test_state = {"projects": {"P1": {"data": "test"}}}
    state_manager.save_state(state_path, test_state)

    loaded = state_manager.load_state(state_path)
    assert loaded == test_state


def test_update_artifact_hashes_integration(temp_dir, monkeypatch):
    # Mock paths to use temp_dir
    raw_dir = temp_dir / "data" / "raw"
    proc_dir = temp_dir / "data" / "processed"
    state_path = temp_dir / "state.yaml"

    raw_dir.mkdir(parents=True)
    proc_dir.mkdir(parents=True)

    (raw_dir / "file1.csv").write_text("raw_data")
    (proc_dir / "result.json").write_text('{"status": "ok"}')

    monkeypatch.setattr(state_manager, "DATA_RAW_PATH", raw_dir)
    monkeypatch.setattr(state_manager, "DATA_PROCESSED_PATH", proc_dir)
    monkeypatch.setattr(state_manager, "PROJECT_STATE_PATH", state_path)

    project_id = "TEST-PROJ"
    result = state_manager.update_artifact_hashes(project_id)

    assert "data_raw" in result
    assert "data_processed" in result
    assert "file1.csv" in result["data_raw"]
    assert "result.json" in result["data_processed"]


def test_verify_artifacts(temp_dir, monkeypatch):
    raw_dir = temp_dir / "data" / "raw"
    proc_dir = temp_dir / "data" / "processed"
    state_path = temp_dir / "state.yaml"

    raw_dir.mkdir(parents=True)
    proc_dir.mkdir(parents=True)

    file_path = raw_dir / "test.csv"
    file_path.write_text("test")

    # Save initial state
    initial_state = {
        "projects": {
            "TEST-PROJ": {
                "data_raw": {"test.csv": hashlib.sha256(b"test").hexdigest()},
                "data_processed": {}
            }
        }
    }
    state_manager.save_state(state_path, initial_state)

    monkeypatch.setattr(state_manager, "DATA_RAW_PATH", raw_dir)
    monkeypatch.setattr(state_manager, "DATA_PROCESSED_PATH", proc_dir)
    monkeypatch.setattr(state_manager, "PROJECT_STATE_PATH", state_path)

    assert state_manager.verify_artifacts("TEST-PROJ") is True

    # Corrupt the file content
    file_path.write_text("changed")
    assert state_manager.verify_artifacts("TEST-PROJ") is False
