"""
Integration test for the ``--step download_and_align`` CLI entry point.
It runs the download_and_align step using mock data (CI_MODE=1) and checks
that the expected aligned matrix file is created.
"""

import json
from pathlib import Path

import pytest

def test_download_and_align_creates_aligned_matrix(monkeypatch, tmp_path):
    # Point the project root to a temporary location
    monkeypatch.setattr("code.cli.main.PROJECT_ROOT", tmp_path)

    # Ensure CI_MODE is enabled so that mock data is used
    monkeypatch.setenv("CI_MODE", "1")

    # Run the CLI step
    from code.cli.main import main
    import sys

    test_args = ["prog", "--step", "download_and_align"]
    monkeypatch.setattr(sys, "argv", test_args)

    # Execute
    main()

    # Verify that the aligned matrix was written
    aligned_path = tmp_path / "data" / "processed" / "aligned_matrix.csv"
    assert aligned_path.is_file()

    # Verify that its hash was recorded in the state file
    from utils.artifact import _load_state
    state = _load_state()
    rel = aligned_path.resolve().relative_to(tmp_path)
    assert str(rel) in state
