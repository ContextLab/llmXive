"""
Unit test for verification of the checksumming utility (Task T020).

This test reads the checksum manifest file ``data/checksums.txt`` which is
expected to contain lines of the form::

    <checksum>  <relative_path>

for each artifact saved under the repository. For each entry the test
recomputes the SHA‑256 checksum of the referenced file using the
``compute_file_checksum`` helper from ``utils.io`` and asserts that it matches
the recorded value.

The test will fail if:
  * the manifest file does not exist,
  * any listed file is missing,
  * the computed checksum differs from the recorded one.
"""

import pathlib
from typing import List, Tuple

import pytest

from utils.io import compute_file_checksum

# Path to the checksum manifest relative to the repository root.
CHECKSUM_MANIFEST = pathlib.Path("data/checksums.txt")


def _parse_checksum_file(path: pathlib.Path) -> List[Tuple[str, pathlib.Path]]:
    """
    Parse a checksum manifest file.

    Each non‑empty line should contain a SHA‑256 checksum followed by a
    whitespace‑separated relative path to the artifact. Lines starting with
    ``#`` are ignored as comments.

    Returns
    -------
    List[Tuple[str, pathlib.Path]]
        A list of (checksum, absolute_path) tuples.
    """
    entries: List[Tuple[str, pathlib.Path]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Split on whitespace; the first token is the checksum,
            # the remainder (joined) is the path (to allow spaces in paths).
            parts = line.split()
            if len(parts) < 2:
                raise ValueError(f"Malformed checksum line: {line!r}")
            checksum = parts[0]
            rel_path = " ".join(parts[1:])
            artifact_path = pathlib.Path(rel_path)
            # Resolve relative to repository root for consistency.
            entries.append((checksum, artifact_path))
    return entries


class TestChecksummingVerification:
    """
    Test suite that verifies recorded checksums match actual file contents.
    """

    def test_checksums_match(self):
        """
        Re‑compute the SHA‑256 checksum for each file listed in the manifest
        and compare it to the recorded value.
        """
        # Ensure the manifest exists.
        assert CHECKSUM_MANIFEST.is_file(), (
            f"Checksum manifest not found at expected location: {CHECKSUM_MANIFEST}"
        )

        entries = _parse_checksum_file(CHECKSUM_MANIFEST)

        # Guard against an empty manifest – the test would be meaningless.
        assert entries, "Checksum manifest is empty; no files to verify."

        mismatches: List[Tuple[pathlib.Path, str, str]] = []

        for recorded_checksum, rel_path in entries:
            # Resolve the path relative to the repository root.
            artifact_path = pathlib.Path(rel_path)
            assert artifact_path.is_file(), (
                f"Artifact listed in checksum manifest does not exist: {artifact_path}"
            )
            actual_checksum = compute_file_checksum(artifact_path)
            if actual_checksum != recorded_checksum:
                mismatches.append((artifact_path, recorded_checksum, actual_checksum))

        # If any mismatches were found, raise an informative assertion error.
        assert not mismatches, (
            "Checksum verification failed for the following files:\n"
            + "\n".join(
                f"{p}: expected {exp}, got {got}"
                for p, exp, got in mismatches
            )
        )