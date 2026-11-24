"""
Test suite for the ``code.bootstrap`` script.

The test verifies that:
1. ``bootstrap.main()`` returns exit code 0.
2. The required project directories are created under a patched
   ``paths.root``.
3. The pinned ``requirements.txt`` written by the script matches the
   expected content defined in ``bootstrap._REQUIREMENTS``.
"""
import os
from pathlib import Path

import pytest

from llmxive_toolkit import paths
from code import bootstrap


@pytest.fixture
def temp_root(tmp_path, monkeypatch):
    """Patch ``paths.root`` to point at a temporary directory."""
    monkeypatch.setattr(paths, "root", Path(tmp_path))
    # Ensure helper functions that rely on ``paths.root`` see the patch
    return Path(tmp_path)


def test_bootstrap_creates_structure_and_requirements(temp_root):
    # Run the bootstrap script
    exit_code = bootstrap.main()
    assert exit_code == 0, "Bootstrap script should exit with code 0"

    # Expected top‑level directories
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
        assert d.is_dir(), f"Expected directory {d} to exist"

    # Verify the requirements file matches the pinned list
    req_path = temp_root / "requirements.txt"
    assert req_path.is_file(), "requirements.txt should be created at project root"

    with open(req_path, "r", encoding="utf-8") as f:
        written = f.read().strip()
    expected = bootstrap._REQUIREMENTS.strip()
    assert written == expected, "Pinned requirements.txt content does not match expected"