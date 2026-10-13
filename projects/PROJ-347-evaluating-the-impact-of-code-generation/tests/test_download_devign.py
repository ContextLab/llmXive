"""
Integration test for the Devign download script.

The test invokes ``code.download_devign.main`` which should:
* download the Devign zip archive (if not already present),
* extract ``devign.csv`` to ``data/raw/devign/devign.csv``,
* compute its SHA‑256 checksum,
* store the checksum in ``data/checksums.json``.

After execution the test asserts that the expected files exist and that the
checksum recorded in ``checksums.json`` matches the actual file checksum.
"""
import json
import os

from pathlib import Path

import pytest

# Import the script under test
from code.download_devign import (
    main,
    CSV_DEST,
    CHECKSUMS_PATH,
    compute_sha256,
)

@pytest.mark.timeout(300)
def test_download_and_checksum(tmp_path, monkeypatch):
    """
    Run the download script and verify artefacts.

    The test runs in an isolated temporary directory to avoid side‑effects
    on the real project data. ``llmxive_toolkit.paths`` is monkey‑patched to
    point into ``tmp_path``.
    """
    # ------------------------------------------------------------------
    # Patch the llmxive_toolkit.paths helpers so all file writes go under
    # the temporary directory.
    # ------------------------------------------------------------------
    from llmxive_toolkit import paths as original_paths

    class TempPaths:
        """A minimal stub exposing the same API used by the script."""
        def __init__(self, root: Path):
            self._root = root

        def data(self, *parts):
            p = self._root.joinpath(*parts)
            p.parent.mkdir(parents=True, exist_ok=True)
            return p

    temp_paths = TempPaths(tmp_path)

    monkeypatch.setattr("llmxive_toolkit.paths", temp_paths, raising=False)

    # Ensure a clean state
    assert not CSV_DEST.is_file()
    assert not CHECKSUMS_PATH.is_file()

    # Run the script – this will download the real dataset from the internet.
    main()

    # ------------------------------------------------------------------
    # Assertions
    # ------------------------------------------------------------------
    # CSV must exist
    assert CSV_DEST.is_file(), f"Expected CSV at {CSV_DEST}"
    # Checksums file must exist
    assert CHECKSUMS_PATH.is_file(), f"Expected checksums JSON at {CHECKSUMS_PATH}"

    # Load the recorded checksum and compare with the actual file checksum
    with open(CHECKSUMS_PATH, "r", encoding="utf-8") as f:
        checksums = json.load(f)

    recorded = checksums.get(str(CSV_DEST))
    assert recorded is not None, "Checksum entry missing in checksums.json"

    actual = compute_sha256(CSV_DEST)
    assert recorded == actual, "Recorded checksum does not match actual file checksum"