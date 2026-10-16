"""
Unit tests for the ``code/bootstrap.py`` script.

The test monkey‑patches ``llmxive_toolkit.paths.root`` to a temporary
directory, runs ``bootstrap.main()``, and then checks that:

1. All required directories have been created.
2. A ``requirements.txt`` file exists at the project root.
3. The contents of the requirements file contain at least one of the
   pinned dependencies (e.g. ``torch==``) to ensure the correct file was
   written.
"""

import sys
import importlib

import pytest

def test_bootstrap_creates_structure(tmp_path, monkeypatch):
    # Monkey‑patch the project root used by ``llmxive_toolkit.paths``.
    from llmxive_toolkit import paths

    monkeypatch.setattr(paths, "root", tmp_path, raising=False)

    # Reload the bootstrap module to ensure it picks up the patched root.
    bootstrap = importlib.import_module("code.bootstrap")
    importlib.reload(bootstrap)

    # Run the bootstrap main function. It returns an exit code (0 on success).
    exit_code = bootstrap.main()
    assert exit_code == 0

    # Expected directories relative to the patched root.
    expected_dirs = [
        "code",
        "data/raw",
        "data/interim",
        "data/processed",
        "data/results",
        "code/tests",
        "docs",
    ]

    for rel_dir in expected_dirs:
        dir_path = tmp_path / rel_dir
        assert dir_path.is_dir(), f"Missing directory: {dir_path}"

    # The requirements.txt file should be at the project root.
    req_path = tmp_path / "requirements.txt"
    assert req_path.is_file(), "requirements.txt not found at project root"

    # Verify that the file contains at least one known pinned dependency.
    content = req_path.read_text()
    assert "torch==" in content, "Pinned requirements do not contain expected torch version"