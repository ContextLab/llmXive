"""
Unit tests for project setup verification.
Validates that the required directory structure exists as per T002a.
"""
import os
import pytest
from pathlib import Path


def test_directory_structure_exists():
    """
    Asserts the existence of specific paths required for the project:
    src/data, src/models, data/raw, data/processed, data/interim,
    tests/contract, tests/unit, tests/integration.
    """
    # Determine the project root (parent of the tests directory)
    # Assuming this file is at tests/unit/test_setup.py
    project_root = Path(__file__).resolve().parent.parent.parent

    required_dirs = [
        project_root / "src" / "data",
        project_root / "src" / "models",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "interim",
        project_root / "tests" / "contract",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
    ]

    missing_dirs = []
    for dir_path in required_dirs:
        if not dir_path.is_dir():
            missing_dirs.append(str(dir_path.relative_to(project_root)))

    assert not missing_dirs, (
        f"Project structure incomplete. Missing directories: {', '.join(missing_dirs)}"
    )