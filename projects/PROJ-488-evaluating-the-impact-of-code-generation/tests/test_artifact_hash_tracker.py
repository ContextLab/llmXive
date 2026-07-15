"""
Tests for the artifact_hash_tracker module (Task T038).
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import pytest

# We need to add the code directory to the path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from artifact_hash_tracker import (
    get_artifact_type,
    hash_artifact,
    register_artifact,
    track_all_major_outputs,
    verify_artifact_integrity
)
from state_tracker import load_state_file, save_state_file


@pytest.fixture
def temp_project_structure(tmp_path):
    """Create a temporary project structure for testing."""
    # Create directory structure
    dirs = [
        "data/raw", "data/processed", "data/metrics",
        "results", "results/figures",
        "state/projects"
    ]
    for d in dirs:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)

    # Create some dummy files
    (tmp_path / "data/raw" / "dataset.csv").write_text("id,code\n1,print('hello')")
    (tmp_path / "data/metrics" / "complexity.csv").write_text("id,score\n1,5.0")
    (tmp_path / "results/figures" / "boxplot.png").write_bytes(b"fake_png_data")
    (tmp_path / "results" / "stats.json").write_text('{"p_value": 0.03}')

    # Create a dummy state file
    state_file = tmp_path / "state/projects" / "PROJ-488-evaluating-the-impact-of-code-generation.yaml"
    state_content = {
        "project_id": "PROJ-488-evaluating-the-impact-of-code-generation",
        "created_at": datetime.utcnow().isoformat(),
        "artifact_hashes": []
    }
    import yaml
    with open(state_file, 'w') as f:
        yaml.dump(state_content, f)

    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    yield tmp_path

    os.chdir(original_cwd)


def test_get_artifact_type(tmp_path, temp_project_structure):
    """Test artifact type classification."""
    assert get_artifact_type(temp_project_structure / "data" / "raw" / "dataset.csv") == "dataset"
    assert get_artifact_type(temp_project_structure / "data" / "metrics" / "complexity.csv") == "metric"
    assert get_artifact_type(temp_project_structure / "results" / "figures" / "boxplot.png") == "figure"
    assert get_artifact_type(temp_project_structure / "results" / "stats.json") == "stat"


def test_hash_artifact_file(temp_project_structure):
    """Test hashing a single file."""
    file_path = temp_project_structure / "data" / "raw" / "dataset.csv"
    hash_val = hash_artifact(file_path)
    assert isinstance(hash_val, str)
    assert len(hash_val) == 64  # SHA-256 hex length


def test_hash_artifact_dir(temp_project_structure):
    """Test hashing a directory."""
    dir_path = temp_project_structure / "data" / "raw"
    hash_val = hash_artifact(dir_path)
    assert isinstance(hash_val, str)
    assert len(hash_val) == 64


def test_register_artifact(temp_project_structure):
    """Test registering a single artifact."""
    file_path = temp_project_structure / "data" / "raw" / "dataset.csv"
    state_file = temp_project_structure / "state" / "projects" / "PROJ-488-evaluating-the-impact-of-code-generation.yaml"

    record = register_artifact(file_path, state_file)

    assert "path" in record
    assert "type" in record
    assert "hash" in record
    assert "registered_at" in record
    assert record["type"] == "dataset"

    # Verify it was written to state
    state = load_state_file(state_file)
    assert len(state["artifact_hashes"]) == 1
    assert state["artifact_hashes"][0]["path"] == "data/raw/dataset.csv"


def test_verify_artifact_integrity(temp_project_structure):
    """Test integrity verification."""
    file_path = temp_project_structure / "data" / "raw" / "dataset.csv"
    state_file = temp_project_structure / "state" / "projects" / "PROJ-488-evaluating-the-impact-of-code-generation.yaml"

    # Register first
    record = register_artifact(file_path, state_file)
    expected_hash = record["hash"]

    # Verify success
    assert verify_artifact_integrity(file_path, expected_hash, state_file) is True

    # Verify failure with wrong hash
    assert verify_artifact_integrity(file_path, "wrong_hash", state_file) is False


def test_track_all_major_outputs(temp_project_structure):
    """Test tracking all artifacts in the project."""
    state_file = temp_project_structure / "state" / "projects" / "PROJ-488-evaluating-the-impact-of-code-generation.yaml"

    registered = track_all_major_outputs(state_file)

    # Should have registered at least 4 files (dataset, metrics, stats, figures)
    assert len(registered) >= 4

    # Verify state file was updated
    state = load_state_file(state_file)
    assert len(state["artifact_hashes"]) >= 4


def test_nonexistent_artifact(temp_project_structure):
    """Test handling of non-existent artifact."""
    file_path = temp_project_structure / "data" / "nonexistent.csv"
    state_file = temp_project_structure / "state" / "projects" / "PROJ-488-evaluating-the-impact-of-code-generation.yaml"

    with pytest.raises(FileNotFoundError):
        register_artifact(file_path, state_file)
