"""
Unit tests for the checkpoint mechanism.
"""

import json
import os
import tempfile
from pathlib import Path
from datetime import datetime

import pytest

from src.utils.checkpoint import (
    save_checkpoint,
    load_checkpoint,
    update_checkpoint,
    create_progress_tracker,
    advance_progress,
    finalize_checkpoint,
    CheckpointError,
    CHECKPOINT_SCHEMA_VERSION,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test checkpoints."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def valid_checkpoint_data():
    """Generate valid checkpoint data for testing."""
    return {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "experiment_id": "test_exp_001",
        "task_id": "T024",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": "running",
        "progress": {
            "total_items": 100,
            "processed_items": 50,
            "current_item": 51,
            "percent_complete": 0.5,
        },
        "intermediate_results": [
            {"subset_id": 1, "coeff_variance": 0.05},
            {"subset_id": 2, "coeff_variance": 0.06},
        ],
        "metadata": {
            "dataset_name": "Auto",
            "sample_size_tier": 25,
            "random_seed": 42,
            "model_type": "ols",
        },
        "error_log": [],
    }


def test_save_and_load_checkpoint(temp_dir, valid_checkpoint_data):
    """Test saving and loading a valid checkpoint."""
    checkpoint_path = save_checkpoint(valid_checkpoint_data, checkpoint_dir=temp_dir)

    assert checkpoint_path.exists()

    loaded_data = load_checkpoint(str(checkpoint_path))

    assert loaded_data["experiment_id"] == valid_checkpoint_data["experiment_id"]
    assert loaded_data["task_id"] == valid_checkpoint_data["task_id"]
    assert loaded_data["status"] == valid_checkpoint_data["status"]
    assert loaded_data["schema_version"] == CHECKPOINT_SCHEMA_VERSION


def test_load_checkpoint_missing_file(temp_dir):
    """Test loading a non-existent checkpoint raises error."""
    with pytest.raises(CheckpointError) as exc_info:
        load_checkpoint(os.path.join(temp_dir, "nonexistent.json"))

    assert "not found" in str(exc_info.value).lower()


def test_load_checkpoint_invalid_json(temp_dir):
    """Test loading invalid JSON raises error."""
    invalid_path = os.path.join(temp_dir, "invalid.json")
    with open(invalid_path, "w") as f:
        f.write("{ not valid json }")

    with pytest.raises(CheckpointError) as exc_info:
        load_checkpoint(invalid_path)

    assert "invalid json" in str(exc_info.value).lower()


def test_load_checkpoint_missing_required_field(temp_dir, valid_checkpoint_data):
    """Test loading checkpoint missing required field raises error."""
    del valid_checkpoint_data["experiment_id"]
    checkpoint_path = save_checkpoint(valid_checkpoint_data, checkpoint_dir=temp_dir)

    with pytest.raises(CheckpointError) as exc_info:
        load_checkpoint(str(checkpoint_path))

    assert "missing required field" in str(exc_info.value).lower()


def test_load_checkpoint_schema_mismatch(temp_dir):
    """Test loading checkpoint with wrong schema version raises error."""
    data = {
        "schema_version": "0.9.0",
        "experiment_id": "test",
        "task_id": "T001",
        "timestamp": "2024-01-01T00:00:00Z",
        "status": "running",
        "progress": {},
        "intermediate_results": [],
        "metadata": {},
        "error_log": [],
    }
    checkpoint_path = save_checkpoint(data, checkpoint_dir=temp_dir)

    with pytest.raises(CheckpointError) as exc_info:
        load_checkpoint(str(checkpoint_path))

    assert "schema version mismatch" in str(exc_info.value).lower()


def test_update_checkpoint_status(temp_dir, valid_checkpoint_data):
    """Test updating checkpoint status."""
    checkpoint_path = save_checkpoint(valid_checkpoint_data, checkpoint_dir=temp_dir)

    updated_data = update_checkpoint(str(checkpoint_path), status="completed")

    assert updated_data["status"] == "completed"
    assert updated_data["timestamp"] != valid_checkpoint_data["timestamp"]


def test_update_checkpoint_progress(temp_dir, valid_checkpoint_data):
    """Test updating checkpoint progress."""
    checkpoint_path = save_checkpoint(valid_checkpoint_data, checkpoint_dir=temp_dir)

    new_progress = {
        "total_items": 100,
        "processed_items": 75,
        "current_item": 76,
        "percent_complete": 0.75,
    }

    updated_data = update_checkpoint(str(checkpoint_path), progress=new_progress)

    assert updated_data["progress"]["processed_items"] == 75
    assert updated_data["progress"]["percent_complete"] == 0.75


def test_update_checkpoint_add_result(temp_dir, valid_checkpoint_data):
    """Test updating checkpoint by adding a new result."""
    checkpoint_path = save_checkpoint(valid_checkpoint_data, checkpoint_dir=temp_dir)

    initial_len = len(valid_checkpoint_data["intermediate_results"])

    updated_data = update_checkpoint(str(checkpoint_path), new_result={"key": "value"})

    assert len(updated_data["intermediate_results"]) == initial_len + 1
    assert updated_data["intermediate_results"][-1] == {"key": "value"}


def test_update_checkpoint_add_error(temp_dir, valid_checkpoint_data):
    """Test updating checkpoint by adding an error."""
    checkpoint_path = save_checkpoint(valid_checkpoint_data, checkpoint_dir=temp_dir)

    updated_data = update_checkpoint(str(checkpoint_path), error="Something went wrong")

    assert len(updated_data["error_log"]) == 1
    assert updated_data["error_log"][0] == "Something went wrong"
    assert updated_data["status"] == "failed"


def test_update_checkpoint_metadata(temp_dir, valid_checkpoint_data):
    """Test updating checkpoint metadata."""
    checkpoint_path = save_checkpoint(valid_checkpoint_data, checkpoint_dir=temp_dir)

    metadata_updates = {"new_key": "new_value", "sample_size_tier": 50}

    updated_data = update_checkpoint(str(checkpoint_path), metadata_updates=metadata_updates)

    assert updated_data["metadata"]["new_key"] == "new_value"
    assert updated_data["metadata"]["sample_size_tier"] == 50


def test_create_progress_tracker(temp_dir):
    """Test creating a progress tracker checkpoint."""
    checkpoint_path, initial_count = create_progress_tracker(
        experiment_id="exp_test",
        task_id="T024",
        total_items=100,
        metadata={"dataset": "test"},
        checkpoint_dir=temp_dir,
    )

    assert checkpoint_path.exists()
    assert initial_count == 0

    data = load_checkpoint(str(checkpoint_path))
    assert data["experiment_id"] == "exp_test"
    assert data["task_id"] == "T024"
    assert data["progress"]["total_items"] == 100
    assert data["progress"]["processed_items"] == 0
    assert data["status"] == "running"


def test_advance_progress(temp_dir, valid_checkpoint_data):
    """Test advancing progress in a checkpoint."""
    checkpoint_path = save_checkpoint(valid_checkpoint_data, checkpoint_dir=temp_dir)

    updated_data = advance_progress(str(checkpoint_path), processed_count=60, current_item=61)

    assert updated_data["progress"]["processed_items"] == 60
    assert updated_data["progress"]["current_item"] == 61
    assert updated_data["progress"]["percent_complete"] == 0.6


def test_finalize_checkpoint_completed(temp_dir, valid_checkpoint_data):
    """Test finalizing a checkpoint as completed."""
    checkpoint_path = save_checkpoint(valid_checkpoint_data, checkpoint_dir=temp_dir)

    final_data = finalize_checkpoint(str(checkpoint_path), status="completed")

    assert final_data["status"] == "completed"


def test_finalize_checkpoint_with_results(temp_dir, valid_checkpoint_data):
    """Test finalizing a checkpoint with final results."""
    checkpoint_path = save_checkpoint(valid_checkpoint_data, checkpoint_dir=temp_dir)

    final_results = [{"final_metric": 0.99}]

    final_data = finalize_checkpoint(str(checkpoint_path), final_results=final_results)

    assert final_data["intermediate_results"][-1] == {"final_metric": 0.99}


def test_save_checkpoint_missing_required_field():
    """Test saving checkpoint missing required field raises error."""
    data = {
        "task_id": "T001",
        "timestamp": "2024-01-01T00:00:00Z",
        "status": "running",
        "progress": {},
        "intermediate_results": [],
        "metadata": {},
        "error_log": [],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(CheckpointError) as exc_info:
            save_checkpoint(data, checkpoint_dir=tmpdir)

        assert "missing required field" in str(exc_info.value).lower()


def test_save_checkpoint_invalid_data():
    """Test saving checkpoint with non-serializable data raises error."""
    data = {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "experiment_id": "test",
        "task_id": "T001",
        "timestamp": "2024-01-01T00:00:00Z",
        "status": "running",
        "progress": {},
        "intermediate_results": [],
        "metadata": {},
        "error_log": [],
        "invalid_obj": object(),  # Not JSON serializable
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(CheckpointError) as exc_info:
            save_checkpoint(data, checkpoint_dir=tmpdir)

        assert "failed to serialize" in str(exc_info.value).lower()