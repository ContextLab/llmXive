"""
Unit tests for linting configuration files.
"""
import os
import tempfile
from pathlib import Path

import pytest


def test_flake8_exists_and_valid():
    """Verify .flake8 exists and contains expected configuration."""
    project_root = Path(__file__).resolve().parent.parent.parent / "projects" / "PROJ-227-assessing-the-trade-offs-between-static-"
    flake8_path = project_root / ".flake8"

    assert flake8_path.exists(), ".flake8 file not found"

    content = flake8_path.read_text()
    assert "max-line-length = 88" in content, "max-line-length 88 not found in .flake8"


def test_pyproject_black_config():
    """Verify pyproject.toml exists and contains Black configuration."""
    project_root = Path(__file__).resolve().parent.parent.parent / "projects" / "PROJ-227-assessing-the-trade-offs-between-static-"
    pyproject_path = project_root / "pyproject.toml"

    assert pyproject_path.exists(), "pyproject.toml file not found"

    content = pyproject_path.read_text()
    assert "[tool.black]" in content, "[tool.black] section not found in pyproject.toml"
    assert "line-length = 88" in content, "line-length 88 not found in pyproject.toml [tool.black]"