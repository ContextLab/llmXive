"""
Integration test to verify the complete project directory structure.
"""
import os
import pytest
from pathlib import Path


def test_directory_structure_requirements():
    """
    Comprehensive check for all required directories (T001a, T001b, T001c).
    """
    root = Path(__file__).parent.parent.parent

    # T001a: Data directories
    data_dirs = [
        "data/raw",
        "data/distorted",
        "data/outputs",
        "data/metadata",
        "output/control",
    ]

    # T001b: Source directories
    src_dirs = [
        "src/generators",
        "src/inference",
        "src/analysis",
    ]

    # T001c: Test directories
    test_dirs = [
        "tests/unit",
        "tests/integration",
    ]

    all_dirs = data_dirs + src_dirs + test_dirs

    missing = []
    for d in all_dirs:
        path = root / d
        if not path.exists() or not path.is_dir():
            missing.append(str(path))

    assert not missing, f"Missing required directories: {missing}"
