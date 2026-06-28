"""
Integration test for the checksum manifest utilities.

This test verifies that the checksum computation utilities work together
correctly on a real file. It creates a temporary file, computes its checksum
using the public API, and checks that the resulting mapping contains the
expected entry.
"""

import pathlib
import tempfile

import pytest

# Import the public functions from the checksum_manifest module as defined in the
# project's API surface.
from code.checksum_manifest import (
    compute_all_artifact_checksums,
    compute_file_checksum,
    get_artifact_hashes,
)


@pytest.fixture
def temporary_file():
    """Create a temporary file with known content and return its Path."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = pathlib.Path(tmp_dir) / "sample.txt"
        # Write deterministic content so the checksum is reproducible.
        tmp_path.write_text("checksum integration test content", encoding="utf-8")
        yield tmp_path
    # TemporaryDirectory cleans up automatically.


def test_compute_file_checksum_matches_known_value(temporary_file):
    """
    Verify that ``compute_file_checksum`` returns a non‑empty hex string and that
    calling it twice on the same file yields identical results.
    """
    first = compute_file_checksum(str(temporary_file))
    second = compute_file_checksum(str(temporary_file))

    # The checksum should be a non‑empty string (hex representation).
    assert isinstance(first, str) and len(first) > 0
    # Re‑computing must give the same value.
    assert first == second


def test_compute_all_artifact_checksums_returns_mapping(temporary_file):
    """
    ``compute_all_artifact_checksums`` should accept an iterable of file paths
    (as strings) and return a dictionary mapping each path to its checksum.
    """
    checksums = compute_all_artifact_checksums([str(temporary_file)])

    # The result must be a dict containing exactly one entry.
    assert isinstance(checksums, dict)
    assert len(checksums) == 1
    assert str(temporary_file) in checksums

    # The checksum value should match the one obtained via the single‑file API.
    expected = compute_file_checksum(str(temporary_file))
    assert checksums[str(temporary_file)] == expected


def test_get_artifact_hashes_returns_dict():
    """
    ``get_artifact_hashes`` should always return a dictionary (possibly empty)
    representing the current manifest state. The test does not depend on prior
    state; it merely asserts the return type.
    """
    artifact_hashes = get_artifact_hashes()
    assert isinstance(artifact_hashes, dict)