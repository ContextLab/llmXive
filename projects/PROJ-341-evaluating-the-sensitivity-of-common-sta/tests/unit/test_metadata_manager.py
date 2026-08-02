"""Unit tests for the metadata manager."""
import os
import json
import tempfile
import pytest

# Monkey-patch the metadata file path for testing
import code.utils.metadata_manager as mm_module

@pytest.fixture
def temp_metadata_dir(tmp_path):
    """Create a temporary directory for metadata files."""
    original_path = mm_module.METADATA_FILE_PATH
    test_path = str(tmp_path / "test_simulation_metadata.json")
    mm_module.METADATA_FILE_PATH = test_path
    yield test_path
    mm_module.METADATA_FILE_PATH = original_path


def test_ensure_metadata_file_exists_creates_file(temp_metadata_dir):
    """Test that ensure_metadata_file_exists creates the file if missing."""
    if os.path.exists(temp_metadata_dir):
        os.remove(temp_metadata_dir)

    result = mm_module.ensure_metadata_file_exists()
    assert result == temp_metadata_dir
    assert os.path.exists(temp_metadata_dir)

    with open(temp_metadata_dir, 'r') as f:
        data = json.load(f)
    assert "runs" in data
    assert "datasets" in data
    assert "created_at" in data


def test_load_simulation_metadata(temp_metadata_dir):
    """Test loading metadata."""
    mm_module.ensure_metadata_file_exists()
    data = mm_module.load_simulation_metadata()
    assert isinstance(data, dict)
    assert "runs" in data


def test_compute_file_checksum(temp_metadata_dir):
    """Test checksum computation."""
    test_file = os.path.join(os.path.dirname(temp_metadata_dir), "test_checksum.txt")
    with open(test_file, 'w') as f:
        f.write("test content")

    checksum = mm_module.compute_file_checksum(test_file)
    assert len(checksum) == 64  # SHA-256 hex length
    assert checksum == mm_module.compute_file_checksum(test_file)  # Deterministic

    os.remove(test_file)


def test_verify_checksum(temp_metadata_dir):
    """Test checksum verification."""
    test_file = os.path.join(os.path.dirname(temp_metadata_dir), "verify_test.txt")
    with open(test_file, 'w') as f:
        f.write("verify content")

    checksum = mm_module.compute_file_checksum(test_file)
    assert mm_module.verify_checksum(test_file, checksum) is True
    assert mm_module.verify_checksum(test_file, "wrong_checksum") is False

    os.remove(test_file)


def test_register_run(temp_metadata_dir):
    """Test registering a run."""
    mm_module.ensure_metadata_file_exists()
    run_params = {"n": 100, "iterations": 1000}
    run_id = mm_module.register_run(run_params)

    assert run_id is not None
    assert len(run_id) == 36  # UUID length

    data = mm_module.load_simulation_metadata()
    assert len(data["runs"]) == 1
    assert data["runs"][0]["parameters"] == run_params


def test_update_run_status(temp_metadata_dir):
    """Test updating run status."""
    mm_module.ensure_metadata_file_exists()
    run_id = mm_module.register_run({})
    mm_module.update_run_status(run_id, "failed", {"error": "test error"})

    data = mm_module.load_simulation_metadata()
    run = next(r for r in data["runs"] if r["run_id"] == run_id)
    assert run["status"] == "failed"
    assert run["details"]["error"] == "test error"


def test_get_run_history(temp_metadata_dir):
    """Test retrieving run history."""
    mm_module.ensure_metadata_file_exists()
    mm_module.register_run({})
    mm_module.register_run({})

    history = mm_module.get_run_history()
    assert len(history) == 2

    limited = mm_module.get_run_history(limit=1)
    assert len(limited) == 1


def test_register_dataset_checksum(temp_metadata_dir):
    """Test registering a dataset checksum."""
    mm_module.ensure_metadata_file_exists()
    test_file = os.path.join(os.path.dirname(temp_metadata_dir), "dataset.csv")
    with open(test_file, 'w') as f:
        f.write("col1,col2\n1,2")

    mm_module.register_dataset_checksum("test_dataset", test_file, "UCI-123")

    data = mm_module.load_simulation_metadata()
    assert len(data["datasets"]) == 1
    assert data["datasets"][0]["name"] == "test_dataset"
    assert data["datasets"][0]["dataset_id"] == "UCI-123"

    os.remove(test_file)

    # Registering same file again should not duplicate
    mm_module.register_dataset_checksum("test_dataset", test_file, "UCI-123")
    data = mm_module.load_simulation_metadata()
    assert len(data["datasets"]) == 1