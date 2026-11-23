"""
Integration test for the DragMesh‑2 data loader.

The test invokes the loader and checks that:
1. The returned path exists.
2. The file is non‑empty.
3. A SHA‑256 checksum can be computed without error.
"""

import os
from pathlib import Path

import pytest

# Import the loader from the module under test.
from data_loader import load_dragmesh_manifest, get_manifest_checksum

def test_load_dragmesh_manifest_creates_file(tmp_path: Path):
    # Use a temporary directory to avoid polluting the real project data.
    # Monkey‑patch the default location via environment variable.
    original_data_raw = os.getenv("LLMXIVE_DATA_RAW")
    try:
        # Point the llmxive_toolkit paths to the temporary location.
        os.environ["LLMXIVE_DATA_RAW"] = str(tmp_path)

        # Load (this will trigger a download).
        manifest_path = load_dragmesh_manifest()

        # Verify the file exists and is non‑empty.
        assert manifest_path.exists(), "Manifest file was not created."
        assert manifest_path.stat().st_size > 0, "Manifest file is empty."

        # Verify checksum computation works.
        checksum = get_manifest_checksum(manifest_path)
        assert isinstance(checksum, str) and len(checksum) == 64
    finally:
        # Restore any previous environment configuration.
        if original_data_raw is not None:
            os.environ["LLMXIVE_DATA_RAW"] = original_data_raw
        else:
            os.environ.pop("LLMXIVE_DATA_RAW", None)