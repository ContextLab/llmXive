"""
Tests for state management and metadata logging (T011).
"""
import json
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to mock the paths since the code uses relative paths
# We will patch the module's path constants before importing
import code.state_manager as state_manager

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as project root."""
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_dir)

    # Create necessary directories
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    Path("state").mkdir(parents=True, exist_ok=True)

    yield temp_dir

    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)

def test_unresolved_log(temp_project_root):
    """
    Verify that unresolved realizations are logged correctly to
    data/raw/metadata.json and state/unresolved_log.json.
    """
    # Reset state
    state_manager._METADATA_FILE = Path("data/raw/metadata.json")
    state_manager._UNRESOLVED_LOG_FILE = Path("state/unresolved_log.json")

    # Log a single unresolved realization
    state_manager.log_unresolved_realization(
        realization_id=1,
        delta=0.5,
        L=20,
        reason="Convergence failure: TEBD did not converge within max iterations"
    )

    # Verify data/raw/metadata.json
    metadata_path = Path("data/raw/metadata.json")
    assert metadata_path.exists(), "metadata.json was not created"

    with open(metadata_path, 'r') as f:
        metadata = json.load(f)

    assert "unresolved_realizations" in metadata
    assert len(metadata["unresolved_realizations"]) == 1

    entry = metadata["unresolved_realizations"][0]
    assert entry["realization_id"] == 1
    assert entry["delta"] == 0.5
    assert entry["L"] == 20
    assert "Convergence failure" in entry["reason"]
    assert "timestamp" in entry

    # Verify state/unresolved_log.json
    state_log_path = Path("state/unresolved_log.json")
    assert state_log_path.exists(), "unresolved_log.json was not created"

    with open(state_log_path, 'r') as f:
        state_log = json.load(f)

    assert "entries" in state_log
    assert len(state_log["entries"]) == 1
    assert state_log["entries"][0]["realization_id"] == 1
    assert "last_updated" in state_log

def test_batch_logging(temp_project_root):
    """Test batch logging of unresolved realizations."""
    state_manager._METADATA_FILE = Path("data/raw/metadata.json")
    state_manager._UNRESOLVED_LOG_FILE = Path("state/unresolved_log.json")

    # Clear previous logs
    state_manager.clear_unresolved_log()

    # Log a batch
    state_manager.log_unresolved_batch(
        batch_id="batch_001",
        deltas=[0.1, 0.2, 0.3],
        L=30,
        reasons=["Convergence failure", "Memory limit", "Convergence failure"],
        count=3
    )

    # Check metadata
    with open(Path("data/raw/metadata.json"), 'r') as f:
        metadata = json.load(f)

    assert "unresolved_batches" in metadata
    assert len(metadata["unresolved_batches"]) == 1
    assert metadata["unresolved_batches"][0]["batch_id"] == "batch_001"
    assert metadata["unresolved_batches"][0]["count"] == 3

    # Check state log
    with open(Path("state/unresolved_log.json"), 'r') as f:
        state_log = json.load(f)

    assert "batches" in state_log
    assert len(state_log["batches"]) == 1

def test_summary_generation(temp_project_root):
    """Test that summary statistics are generated correctly."""
    state_manager._METADATA_FILE = Path("data/raw/metadata.json")
    state_manager._UNRESOLVED_LOG_FILE = Path("state/unresolved_log.json")

    state_manager.clear_unresolved_log()

    # Add some data
    state_manager.log_unresolved_realization(1, 0.5, 20, "Reason A")
    state_manager.log_unresolved_realization(2, 0.5, 20, "Reason A")
    state_manager.log_unresolved_realization(3, 0.8, 20, "Reason B")

    summary = state_manager.get_unresolved_summary()

    assert summary["total_unresolved"] == 3
    assert summary["count_by_reason"]["Reason A"] == 2
    assert summary["count_by_reason"]["Reason B"] == 1
    assert summary["count_by_delta"][0.5] == 2
    assert summary["count_by_delta"][0.8] == 1

def test_filtering_by_delta(temp_project_root):
    """Test filtering unresolved entries by delta."""
    state_manager._METADATA_FILE = Path("data/raw/metadata.json")
    state_manager._UNRESOLVED_LOG_FILE = Path("state/unresolved_log.json")

    state_manager.clear_unresolved_log()

    state_manager.log_unresolved_realization(1, 0.5, 20, "Reason A")
    state_manager.log_unresolved_realization(2, 0.8, 20, "Reason B")
    state_manager.log_unresolved_realization(3, 0.5, 20, "Reason C")

    filtered = state_manager.get_unresolved_by_delta(0.5)
    assert len(filtered) == 2

    filtered_other = state_manager.get_unresolved_by_delta(0.8)
    assert len(filtered_other) == 1

def test_filtering_by_reason(temp_project_root):
    """Test filtering unresolved entries by reason."""
    state_manager._METADATA_FILE = Path("data/raw/metadata.json")
    state_manager._UNRESOLVED_LOG_FILE = Path("state/unresolved_log.json")

    state_manager.clear_unresolved_log()

    state_manager.log_unresolved_realization(1, 0.5, 20, "Reason A")
    state_manager.log_unresolved_realization(2, 0.8, 20, "Reason B")
    state_manager.log_unresolved_realization(3, 0.5, 20, "Reason A")

    filtered = state_manager.get_unresolved_by_reason("Reason A")
    assert len(filtered) == 2
    assert all(e["reason"] == "Reason A" for e in filtered)

def test_clear_log(temp_project_root):
    """Test clearing the unresolved log."""
    state_manager._METADATA_FILE = Path("data/raw/metadata.json")
    state_manager._UNRESOLVED_LOG_FILE = Path("state/unresolved_log.json")

    # Add data
    state_manager.log_unresolved_realization(1, 0.5, 20, "Reason A")

    # Clear
    state_manager.clear_unresolved_log()

    # Verify empty
    with open(Path("data/raw/metadata.json"), 'r') as f:
        metadata = json.load(f)
    assert len(metadata["unresolved_realizations"]) == 0

    with open(Path("state/unresolved_log.json"), 'r') as f:
        state_log = json.load(f)
    assert len(state_log["entries"]) == 0
