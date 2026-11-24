"""Tests for linting/formatting configuration (T003)."""

import tomllib
from pathlib import Path

from setup_linting import create_gitignore_entries, create_pyproject_config

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_pyproject_has_ruff_and_black_config(tmp_path):
    create_pyproject_config(tmp_path)
    data = tomllib.loads((tmp_path / "pyproject.toml").read_text())
    assert "ruff" in data["tool"]
    assert "black" in data["tool"]
    assert data["tool"]["ruff"]["line-length"] == 100
    assert data["tool"]["black"]["line-length"] == 100


def test_pyproject_config_idempotent(tmp_path):
    create_pyproject_config(tmp_path)
    create_pyproject_config(tmp_path)
    text = (tmp_path / "pyproject.toml").read_text()
    assert text.count("[tool.ruff]") == 1
    assert text.count("[tool.black]") == 1


def test_pyproject_preserves_existing_content(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'glass-formation'\n"
    )
    create_pyproject_config(tmp_path)
    data = tomllib.loads((tmp_path / "pyproject.toml").read_text())
    assert data["project"]["name"] == "glass-formation"
    assert "ruff" in data["tool"]


def test_gitignore_entries_added(tmp_path):
    create_gitignore_entries(tmp_path)
    text = (tmp_path / ".gitignore").read_text()
    assert ".ruff_cache/" in text


def test_project_root_configured():
    pyproject = PROJECT_ROOT / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml must exist in project root"
    data = tomllib.loads(pyproject.read_text())
    assert "ruff" in data["tool"], "pyproject.toml missing [tool.ruff]"
    assert "black" in data["tool"], "pyproject.toml missing [tool.black]"