"""Unit tests verifying the T001 project scaffolding (Phase 0)."""

from pathlib import Path

from llmxive_toolkit import paths

from scaffold import scaffold

REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "data/artifacts",
    "tests/unit",
    "tests/contract",
    "contracts",
]

REQUIRED_FILES = [
    "code/__init__.py",
    "data/raw/.gitkeep",
    "data/processed/.gitkeep",
    "data/artifacts/.gitkeep",
    "tests/unit/.gitkeep",
    "tests/contract/.gitkeep",
]


def test_required_directories_exist():
    for rel in REQUIRED_DIRS:
        assert (paths.root / rel).is_dir(), f"missing directory: {rel}"


def test_required_placeholder_files_exist():
    for rel in REQUIRED_FILES:
        assert (paths.root / rel).is_file(), f"missing file: {rel}"


def test_scaffold_is_idempotent():
    scaffold(paths.root)
    # Structure must still be intact after a re-run.
    for rel in REQUIRED_DIRS:
        assert (paths.root / rel).is_dir()
    for rel in REQUIRED_FILES:
        assert (paths.root / rel).is_file()


def test_code_init_is_valid_python():
    init = paths.root / "code" / "__init__.py"
    compile(init.read_text(encoding="utf-8"), str(init), "exec")