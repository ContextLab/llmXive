import os
import pytest
from pathlib import Path
from config import get_project_root

def get_required_dirs():
    """Returns the list of required directories for Phase 1 setup."""
    return [
        "data/raw",
        "data/processed",
        "code",
        "outputs",
        "tests",
        "state/projects",
        "code/models",
    ]

def test_phase1_directories_exist():
    """
    Test that all Phase 1 directories created by T001a-T001g exist.
    This satisfies the verification requirement for T001h.
    """
    root = get_project_root()
    base_path = Path(root)
    required = get_required_dirs()

    missing = []
    for dir_name in required:
        full_path = base_path / dir_name
        if not full_path.exists():
            missing.append(dir_name)
        elif not full_path.is_dir():
            missing.append(f"{dir_name} (exists but is not a directory)")

    assert len(missing) == 0, f"Missing required directories: {missing}"

def test_init_files_exist():
    """
    Test that __init__.py files exist in Python package directories.
    This satisfies the requirement for T001i.
    """
    root = get_project_root()
    base_path = Path(root)
    package_dirs = ["code", "tests", "code/utils"]

    missing_init = []
    for pkg_dir in package_dirs:
        full_path = base_path / pkg_dir
        init_file = full_path / "__init__.py"
        if not init_file.exists():
            missing_init.append(str(init_file))

    assert len(missing_init) == 0, f"Missing __init__.py files: {missing_init}"
