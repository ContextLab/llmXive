import pytest
from pathlib import Path

def test_required_directories_exist(project_root):
    required_dirs = [
        "src",
        "src/ingestion",
        "src/preprocessing",
        "src/analysis",
        "src/utils",
        "tests",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "data/raw",
        "data/processed",
        "data/processed/results",
        "docs",
        "state"
    ]
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        assert full_path.exists(), f"Directory missing: {full_path}"
        assert full_path.is_dir(), f"Not a directory: {full_path}"

def test_test_directories_exist(project_root):
    test_dirs = [
        "tests",
        "tests/contract",
        "tests/integration",
        "tests/unit"
    ]
    for dir_path in test_dirs:
        full_path = project_root / dir_path
        assert full_path.exists(), f"Test directory missing: {full_path}"