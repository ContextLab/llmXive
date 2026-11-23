"""Tests for the T061 checksum computation script."""

import hashlib
import os
import tempfile
from pathlib import Path

import pytest

# Import the functions from the implementation script
from code.T061_compute_checksum import (
    compute_sha256,
    record_checksum,
    load_state,
    save_state,
)


@pytest.fixture
def temporary_descriptor(tmp_path: Path):
    """Create a temporary descriptor CSV file with deterministic content."""
    content = "col1,col2\n1,2\n3,4\n"
    descriptor_path = tmp_path / "hea_descriptors.csv"
    descriptor_path.write_text(content, encoding="utf-8")
    return descriptor_path


@pytest.fixture
def temporary_state_file(tmp_path: Path):
    """Create an empty temporary state YAML file."""
    state_path = tmp_path / "state.yaml"
    # Ensure the file exists but is empty
    state_path.write_text("", encoding="utf-8")
    return state_path


def test_compute_sha256_matches_manual(temporary_descriptor: Path):
    """The SHA256 computed by the helper must match a manually calculated hash."""
    expected = hashlib.sha256(temporary_descriptor.read_bytes()).hexdigest()
    assert compute_sha256(temporary_descriptor) == expected


def test_record_checksum_updates_state(
    temporary_descriptor: Path, temporary_state_file: Path
):
    """After recording, the state file must contain the correct checksum."""
    checksum = record_checksum(
        descriptor_path=temporary_descriptor, state_path=temporary_state_file
    )
    # Load the state file and verify structure
    state = load_state(temporary_state_file)
    assert "artifact_hashes" in state
    rel_path = str(temporary_descriptor.as_posix())
    assert state["artifact_hashes"][rel_path] == checksum
    # Double‑check that the stored checksum equals the manual hash
    manual = hashlib.sha256(temporary_descriptor.read_bytes()).hexdigest()
    assert checksum == manual


def test_save_and_load_state_roundtrip(tmp_path: Path):
    """Saving a populated state dict and re‑loading it should preserve data."""
    state_path = tmp_path / "state.yaml"
    original_state = {"artifact_hashes": {"a/b.csv": "deadbeef"}}
    save_state(original_state, state_path)
    loaded = load_state(state_path)
    assert loaded == original_state
