"""
Unit test for ``code.utils.setup_dirs``.

The test invokes the ``main`` function, then checks that the verification
manifest exists and that it contains entries for all required directories.
"""

import json
from pathlib import Path

import pytest

# Import the module under test
from code.utils import setup_dirs

def test_setup_dirs_creates_manifest_and_directories(tmp_path, monkeypatch):
    """
    Ensure that the setup script creates the required hierarchy and writes a
    correct JSON manifest.
    """
    # Use the real project root (paths.root) – the script itself uses
    # ``paths`` which already points to the repository root, so we do not
    # need to monkey‑patch anything for this test.
    # Run the main function; it should be idempotent.
    setup_dirs.main()

    # Path to the manifest file
    manifest_path = Path(setup_dirs.paths.state("setup_dirs_verified.json"))

    # The file must exist and be non‑empty
    assert manifest_path.is_file(), "Manifest file was not created"
    assert manifest_path.stat().st_size > 0, "Manifest file is empty"

    # Load the JSON content
    with manifest_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # The manifest should be a list of dicts
    assert isinstance(data, list), "Manifest JSON should be a list"

    # Gather the set of absolute paths present in the manifest
    manifest_paths = {entry["path"] for entry in data if "path" in entry}

    # Verify that each required directory is listed in the manifest
    for required_dir in setup_dirs.REQUIRED_DIRS:
        abs_path = str(required_dir.resolve())
        assert (
            abs_path in manifest_paths
        ), f"Required directory {abs_path} missing from manifest"

    # Additionally, ensure that each required directory actually exists on disk
    for required_dir in setup_dirs.REQUIRED_DIRS:
        assert required_dir.is_dir(), f"Directory {required_dir} does not exist"

# The test can be run directly via ``pytest -q tests/unit/test_setup_dirs.py``.