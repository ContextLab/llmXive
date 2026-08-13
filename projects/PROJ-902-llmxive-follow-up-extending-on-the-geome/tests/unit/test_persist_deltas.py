"""
Unit tests for ``src.data.persist_deltas``.

The tests create a temporary source directory with a tiny dummy delta file,
invoke ``persist_deltas`` and then verify:

1. The file was copied to the destination directory.
2. A ``checksums.txt`` manifest was written.
3. The recorded checksum matches the SHA‑256 digest of the file's contents.
"""

import hashlib
from pathlib import Path

import pytest

from src.data.persist_deltas import persist_deltas


@pytest.fixture
def dummy_delta(tmp_path: Path) -> Path:
    """Create a single dummy delta file with deterministic content."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    delta_file = src_dir / "layer_0.pt"
    # The content does not need to be a real torch tensor; any bytes are fine.
    delta_file.write_bytes(b"dummy-weight-delta")
    return src_dir


def test_persist_deltas_copies_file_and_writes_checksums(tmp_path: Path, dummy_delta: Path):
    dest_dir = tmp_path / "dest"
    # Run the persistence logic.
    checksums = persist_deltas(dummy_delta, dest_dir)

    # 1. The file must exist in the destination.
    expected_file = dest_dir / "layer_0.pt"
    assert expected_file.is_file(), "Delta file was not copied to destination"

    # 2. A checksums manifest must be present.
    checksum_manifest = dest_dir / "checksums.txt"
    assert checksum_manifest.is_file(), "Checksum manifest was not created"

    # 3. The checksum recorded for the file matches a manually computed hash.
    # ``compute_all_checksums`` uses relative file names, so we look up by the
    # basename.
    recorded_hash = checksums.get("layer_0.pt")
    assert recorded_hash is not None, "Checksum for the copied file missing in result mapping"

    # Manual SHA‑256 computation.
    manual_hash = hashlib.sha256(b"dummy-weight-delta").hexdigest()
    assert recorded_hash == manual_hash, "Recorded checksum does not match file contents"