"""
Test suite for the bootstrap script (T001).

This test verifies that:
1. The bootstrap script creates the required directory layout.
2. The pinned requirements.txt is written correctly.
3. The script exits with a status code of 0.

The test runs the bootstrap script in an isolated temporary directory by
monkey‑patching ``llmxive_toolkit.paths.root``.
"""

import importlib
import pytest
from pathlib import Path


def test_bootstrap_creates_structure(tmp_path, monkeypatch):
    # Monkey‑patch the project root used by llmxive_toolkit.paths
    from llmxive_toolkit import paths
    monkeypatch.setattr(paths, "root", tmp_path, raising=False)

    # Import the bootstrap module after the root has been patched
    # ``code`` is now a package because of ``code/__init__.py``
    bootstrap = importlib.import_module("code.bootstrap")

    # Run the main entry point and capture the SystemExit exception
    with pytest.raises(SystemExit) as excinfo:
        bootstrap.main()
    assert excinfo.value.code == 0, "Bootstrap should exit with code 0"

    # Expected directories (as defined in the bootstrap script)
    expected_dirs = [
        paths.code(),
        paths.data("raw"),
        paths.data("interim"),
        paths.data("processed"),
        paths.data("results"),
        paths.code("tests"),
        paths.docs(),
    ]

    for d in expected_dirs:
        assert d.is_dir(), f"Expected directory not created: {d}"

    # Verify the pinned requirements file exists and matches the script's constant
    req_path = paths.code("requirements.txt")
    assert req_path.is_file(), "requirements.txt was not created"
    written_content = req_path.read_text().strip()

    # Access the private constant from the bootstrap module for comparison
    expected_content = bootstrap._REQUIREMENTS.strip()
    assert (
        written_content == expected_content
    ), "requirements.txt content does not match the pinned list"

    # Optionally, ensure the directory tree was printed (stdout capture not needed here)