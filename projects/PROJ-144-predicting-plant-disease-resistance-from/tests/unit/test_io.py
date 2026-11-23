import os
import yaml
import logging
from pathlib import Path
import pytest
import tempfile
import shutil

from code.utils.io import compute_file_hash, log_artifact, log_data_acquisition_step, log_preprocessing_step
from code.utils.constants import STATE_DIR

@pytest.fixture
def temp_state_dir():
    """Create a temporary directory to simulate STATE_DIR for testing."""
    temp_dir = tempfile.mkdtemp()
    # Monkey-patch STATE_DIR for the duration of the test
    original_state_dir = STATE_DIR
    # We cannot easily monkey-patch a module-level constant used in function definitions,
    # so we will rely on the fact that STATE_DIR is a Path object.
    # Instead, we will test by creating files in the temp dir and manually calling the logic
    # or by temporarily replacing the global STATE_DIR if possible.
    # A simpler approach for this specific test: use the actual STATE_DIR but clean up after.
    # However, to avoid polluting the real state, we'll test the logic in isolation.
    # Let's just test the functions that don't depend on the global STATE_DIR path directly
    # or mock the path.
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_compute_file_hash(tmp_path):
    """Test hash computation for a known file."""
    test_file = tmp_path / "test.txt"
    test_content = b"Hello, World!"
    test_file.write_bytes(test_content)

    hash_val = compute_file_hash(test_file, algorithm="sha256")
    assert isinstance(hash_val, str)
    assert len(hash_val) == 64  # SHA256 hex length

def test_log_data_acquisition_step(tmp_path, monkeypatch):
    """Test logging a data acquisition step."""
    # Monkeypatch STATE_DIR to point to temp directory
    from code.utils import io
    original_state_dir = io.STATE_DIR
    io.STATE_DIR = Path(tmp_path)

    try:
        step_name = "download_study"
        details = {"study_id": "C-STUDY-123", "status": "success", "files_downloaded": 2}
        
        log_data_acquisition_step(step_name, details)

        log_file = tmp_path / "data_log.yaml"
        assert log_file.exists()

        with open(log_file, "r") as f:
            logs = yaml.safe_load(f)

        assert isinstance(logs, list)
        assert len(logs) == 1
        assert logs[0]["step"] == step_name
        assert logs[0]["details"]["study_id"] == "C-STUDY-123"
    finally:
        io.STATE_DIR = original_state_dir

def test_log_preprocessing_step(tmp_path, monkeypatch):
    """Test logging a preprocessing step."""
    from code.utils import io
    original_state_dir = io.STATE_DIR
    io.STATE_DIR = Path(tmp_path)

    try:
        step_name = "log_transform"
        details = {"features_before": 1000, "features_after": 850, "missing_threshold": 0.3}

        log_preprocessing_step(step_name, details)

        log_file = tmp_path / "preprocessing_log.yaml"
        assert log_file.exists()

        with open(log_file, "r") as f:
            logs = yaml.safe_load(f)

        assert isinstance(logs, list)
        assert len(logs) == 1
        assert logs[0]["step"] == step_name
        assert logs[0]["details"]["features_before"] == 1000
    finally:
        io.STATE_DIR = original_state_dir

def test_log_artifact(tmp_path, monkeypatch):
    """Test logging an artifact with hash."""
    from code.utils import io
    original_state_dir = io.STATE_DIR
    io.STATE_DIR = Path(tmp_path)

    try:
        # Create a dummy artifact file
        artifact_file = tmp_path / "dummy_artifact.csv"
        artifact_file.write_text("col1,col2\n1,2\n3,4")

        log_artifact(artifact_file, "processed_data", "Test artifact for T016")

        state_file = tmp_path / "artifact_hashes.yaml"
        assert state_file.exists()

        with open(state_file, "r") as f:
            records = yaml.safe_load(f)

        assert isinstance(records, list)
        assert len(records) == 1
        assert records[0]["type"] == "processed_data"
        assert "hash" in records[0]
        assert len(records[0]["hash"]) == 64
    finally:
        io.STATE_DIR = original_state_dir