import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest
import yaml

from src.cli.update_project_state import (
    compute_sha256,
    find_artifacts,
    update_project_state,
    main,
)


@pytest.fixture
def temp_project_root():
    """Create a temporary project structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Create directory structure
        (project_root / "data" / "processed").mkdir(parents=True)
        (project_root / "data" / "models").mkdir(parents=True)
        (project_root / "state" / "projects").mkdir(parents=True)
        (project_root / "logs").mkdir(parents=True)

        # Create test artifacts
        parquet_file = project_root / "data" / "processed" / "training_sample.parquet"
        parquet_file.write_bytes(b"fake parquet data")

        pkl_file = project_root / "data" / "models" / "gap_predictor.pkl"
        pkl_file.write_bytes(b"fake pkl data")

        # Create another parquet file
        parquet_file2 = project_root / "data" / "processed" / "split_train.parquet"
        parquet_file2.write_bytes(b"fake parquet data 2")

        yield project_root


def test_compute_sha256():
    """Test SHA-256 computation."""
    with tempfile.NamedTemporaryFile() as tmp:
        tmp.write(b"test data")
        tmp.flush()
        checksum = compute_sha256(Path(tmp.name))
        assert len(checksum) == 64  # SHA-256 hex string length
        assert isinstance(checksum, str)


def test_compute_sha256_file_not_found():
    """Test SHA-256 computation on non-existent file."""
    with pytest.raises(FileNotFoundError):
        compute_sha256(Path("/non/existent/file"))


def test_find_artifacts(temp_project_root):
    """Test artifact finding with glob patterns."""
    patterns = ["data/processed/*.parquet", "data/models/*.pkl"]
    artifacts = find_artifacts(temp_project_root, patterns)

    assert len(artifacts) == 3
    assert any("training_sample.parquet" in str(a) for a in artifacts)
    assert any("gap_predictor.pkl" in str(a) for a in artifacts)
    assert any("split_train.parquet" in str(a) for a in artifacts)


def test_update_project_state(temp_project_root):
    """Test updating project state with artifact checksums."""
    state_file = temp_project_root / "state" / "projects" / "PROJ-997-llmxive-follow-up-extending-the-mirage-o.yaml"

    state = update_project_state(temp_project_root, state_file)

    assert "updated_at" in state
    assert "artifact_hashes" in state
    assert len(state["artifact_hashes"]) == 3

    # Verify checksums are computed
    for path, checksum in state["artifact_hashes"].items():
        assert len(checksum) == 64
        assert isinstance(checksum, str)

    # Verify file was written
    assert state_file.exists()
    with open(state_file, "r") as f:
        written_state = yaml.safe_load(f)

    assert written_state["updated_at"] == state["updated_at"]
    assert written_state["artifact_hashes"] == state["artifact_hashes"]


def test_main_success(temp_project_root, capsys):
    """Test main function execution."""
    state_file = temp_project_root / "state" / "projects" / "PROJ-997-llmxive-follow-up-extending-the-mirage-o.yaml"

    with patch("sys.argv", [
        "update_project_state.py",
        "--project-root", str(temp_project_root),
        "--state-file", str(state_file),
    ]):
        main()

    captured = capsys.readouterr()
    output = json.loads(captured.out)

    assert "updated_at" in output
    assert "artifact_hashes" in output
    assert len(output["artifact_hashes"]) == 3