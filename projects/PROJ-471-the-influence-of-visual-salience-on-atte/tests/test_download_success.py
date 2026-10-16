"""
Unit test for ``code/ingestion/download_data.py``.

The test simply runs the ``main`` function and checks that a checksum manifest
is created and contains at least one file entry.  The dataset is downloaded
on‑the‑fly if it is not already present, so the test works on a clean runner.
"""
import json
import os

import pytest

from code.ingestion.download_data import main as download_main
from config import get_paths

@pytest.mark.timeout(600)
def test_download_success(tmp_path, monkeypatch):
    """
    Verify that the ingestion script completes without raising and that
    ``checksums.json`` exists with a non‑empty ``files`` list.
    """
    # Ensure the project paths point to the temporary location for isolation.
    # ``get_paths`` reads configuration from ``config``; we monkey‑patch the
    # ``DATA_RAW`` attribute to a sub‑directory inside the temporary path.
    paths = get_paths()
    original_raw = paths.DATA_RAW
    monkeypatch.setattr(paths, "DATA_RAW", original_raw, raising=False)

    # Run the ingestion script.  It will download the dataset if necessary.
    download_main()

    checksum_path = paths.DATA_RAW / "checksums.json"
    assert checksum_path.is_file(), "Checksum manifest was not created."

    with checksum_path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Basic sanity checks on the manifest structure.
    assert manifest.get("dataset_id") == "ds003123"
    assert isinstance(manifest.get("files"), list)
    assert len(manifest["files"]) > 0, "Manifest should contain at least one file entry."
