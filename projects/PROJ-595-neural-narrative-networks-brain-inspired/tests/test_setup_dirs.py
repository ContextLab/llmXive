"""Tests for T001: project directory structure."""

from pathlib import Path

from llmxive_toolkit import paths

from code.setup_dirs import setup_directories

REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "data/results",
    "tests",
]


def test_directories_exist():
    setup_directories()
    root = Path(paths.root)
    for d in REQUIRED_DIRS:
        assert (root / d).is_dir(), f"missing directory: {d}"


def test_code_init_exists():
    setup_directories()
    init = Path(paths.root) / "code" / "__init__.py"
    assert init.is_file()
    assert init.read_text(encoding="utf-8").strip() != ""


def test_gitignore_exists():
    gi = Path(paths.root) / ".gitignore"
    assert gi.is_file()
    assert "data/raw/" in gi.read_text(encoding="utf-8")