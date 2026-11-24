"""Smoke test verifying the required project directory layout.

This guards the Phase 1 setup tasks (T001a-T002c): the ``code/`` and
``tests/`` directories and the ``data/raw``, ``data/processed`` and
``data/artifacts`` subdirectories must all exist at the repository root.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_DIRECTORIES = [
    "code",
    "tests",
    "tests/unit",
    "tests/integration",
    "tests/contract",
    "data/raw",
    "data/processed",
    "data/artifacts",
]


def test_required_directories_exist():
    """Every required project directory must exist at the repo root."""
    for rel in REQUIRED_DIRECTORIES:
        target = PROJECT_ROOT / rel
        assert target.is_dir(), f"Missing required directory: {target}"


def test_tests_directory_is_populated():
    """The tests/ tree must contain at least this test file."""
    test_files = list((PROJECT_ROOT / "tests").rglob("test_*.py"))
    assert test_files, "tests/ directory contains no test files"