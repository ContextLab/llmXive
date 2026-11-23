"""
Unit tests for the ``setup_venv`` module.

The tests exercise the public API (create_venv, install_dependencies,
verify_venv, write_setup_log, and main) to ensure the script produces a
``setup_log.txt`` file that contains both a Python version line and a
non‑empty package list.
"""
import os
import sys
import json
import subprocess
from pathlib import Path

import pytest

# Import the module from the project code directory.
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "code"))

from setup_venv import (
    create_venv,
    install_dependencies,
    verify_venv,
    write_setup_log,
    main,
)


@pytest.fixture(scope="function")
def fresh_venv(tmp_path: Path):
    """Create a fresh virtual environment in a temporary directory."""
    venv_path = tmp_path / "venv"
    # Use the module's helper to create the environment.
    assert create_venv(venv_path)
    yield venv_path
    # Cleanup is automatic via the temporary directory fixture.


def test_write_setup_log(tmp_path: Path):
    """The log file must be written and contain exactly the supplied text."""
    log_path = write_setup_log(tmp_path, "sample content")
    assert log_path.is_file()
    assert log_path.read_text() == "sample content"


def test_verify_venv_contains_version_and_packages(fresh_venv: Path):
    """
    After verification, the output must contain a line that starts with
    ``Python`` and at least one line that looks like a package entry.
    """
    success, output = verify_venv(fresh_venv)
    assert success
    lines = output.splitlines()
    # First line should be the Python version.
    assert any(line.startswith("Python") for line in lines)
    # There should be at least one package entry (the ``pip`` package itself).
    assert any("pip" in line.lower() for line in lines)


def test_main_creates_log_file(tmp_path: Path, monkeypatch):
    """
    Run the CLI entry point with a temporary project layout and ensure that
    ``setup_log.txt`` is created and contains the required information.
    """
    # Build a temporary project structure mirroring the real layout.
    project_root = tmp_path / "proj"
    code_dir = project_root / "code"
    code_dir.mkdir(parents=True)
    # Copy the current ``setup_venv.py`` into the temporary code directory.
    src = Path(__file__).resolve().parents[1] / "setup_venv.py"
    dst = code_dir / "setup_venv.py"
    dst.write_bytes(src.read_bytes())

    # Create a minimal ``requirements.txt`` (just ``pip`` – already present).
    (project_root / "requirements.txt").write_text("pip\n", encoding="utf-8")

    # Patch ``Path(__file__).resolve().parents[1]`` inside the module to point
    # at our temporary project root.
    monkeypatch.setattr(
        "setup_venv.Path",
        lambda *args, **kwargs: Path(*args, **kwargs),
    )
    monkeypatch.setattr(
        "setup_venv.__file__",
        str(dst),
    )

    # Run the script.
    exit_code = main()
    assert exit_code == 0

    log_path = project_root / "venv" / "setup_log.txt"
    assert log_path.is_file()
    content = log_path.read_text()
    # Verify required sections.
    assert "Python" in content
    assert "pip" in content.lower()