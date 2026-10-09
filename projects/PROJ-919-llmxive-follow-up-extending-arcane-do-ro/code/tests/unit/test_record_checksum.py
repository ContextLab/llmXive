import json
import sys
import tempfile
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts.record_gold_standard_checksum import (
    compute_sha256,
    record_checksum_in_state,
)


@pytest.fixture
def temp_gold_standard_file():
    """Create a temporary gold standard JSON file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"test_data": "value", "count": 20}, f)
        path = Path(f.name)
    yield path
    path.unlink()


@pytest.fixture
def temp_state_dir():
    """Create a temporary state directory structure."""
    temp_dir = tempfile.mkdtemp()
    project_dir = Path(temp_dir) / "projects" / "PROJ-919-llmxive-follow-up-extending-arcane-do-ro"
    project_dir.mkdir(parents=True)
    yield project_dir
    import shutil

    shutil.rmtree(temp_dir)


def test_compute_sha256(temp_gold_standard_file):
    """Test that compute_sha256 returns a valid hex string of correct length."""
    checksum = compute_sha256(temp_gold_standard_file)
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA256 hex length
    assert all(c in "0123456789abcdef" for c in checksum)


def test_compute_sha256_determinism(temp_gold_standard_file):
    """Test that checksum is deterministic for the same file."""
    checksum1 = compute_sha256(temp_gold_standard_file)
    checksum2 = compute_sha256(temp_gold_standard_file)
    assert checksum1 == checksum2


def test_compute_sha256_file_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        compute_sha256(Path("/nonexistent/path/file.json"))


def test_record_checksum_in_state_creates_file(temp_state_dir):
    """Test that record_checksum_in_state creates the artifact_hashes.json file."""
    mock_artifact_path = Path("/mock/data/gold_standard/human_annotations.json")
    checksum = "a" * 64

    record_checksum_in_state(mock_artifact_path, checksum, str(temp_state_dir.parent.name))

    hash_file = temp_state_dir / "artifact_hashes.json"
    assert hash_file.exists()

    with open(hash_file, "r") as f:
        data = json.load(f)

    assert "human_annotations.json" in data
    assert data["human_annotations.json"]["checksum"] == checksum


def test_record_checksum_in_state_updates_existing(temp_state_dir):
    """Test that record_checksum_in_state updates existing entries."""
    # Create initial state
    hash_file = temp_state_dir / "artifact_hashes.json"
    initial_data = {"old_artifact.json": {"checksum": "b" * 64}}
    with open(hash_file, "w") as f:
        json.dump(initial_data, f)

    mock_artifact_path = Path("/mock/data/gold_standard/human_annotations.json")
    new_checksum = "c" * 64

    record_checksum_in_state(mock_artifact_path, new_checksum, str(temp_state_dir.parent.name))

    with open(hash_file, "r") as f:
        data = json.load(f)

    assert "old_artifact.json" in data
    assert "human_annotations.json" in data
    assert data["human_annotations.json"]["checksum"] == new_checksum
