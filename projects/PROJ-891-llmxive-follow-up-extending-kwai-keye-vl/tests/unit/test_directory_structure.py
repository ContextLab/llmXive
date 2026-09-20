"""
Unit tests to verify the existence and structure of project directories.
This ensures T001a, T001b, and T001c requirements are met.
"""
import os
import pytest
from pathlib import Path


def test_root_directory_exists():
    """Verify the project root is accessible."""
    root = Path(__file__).parent.parent.parent
    assert root.exists(), f"Root directory {root} does not exist."


def test_data_directory_structure():
    """
    Verify data directories created by T001a:
    data/raw, data/distorted, data/outputs, data/metadata
    """
    root = Path(__file__).parent.parent.parent
    data_dirs = [
        "data/raw",
        "data/distorted",
        "data/outputs",
        "data/metadata",
    ]
    for d in data_dirs:
        path = root / d
        assert path.exists(), f"Missing required directory: {path}"
        assert path.is_dir(), f"Path is not a directory: {path}"


def test_output_control_directory_exists():
    """
    Verify output/control directory created by T001a.
    """
    root = Path(__file__).parent.parent.parent
    path = root / "output" / "control"
    assert path.exists(), f"Missing required directory: {path}"
    assert path.is_dir(), f"Path is not a directory: {path}"


def test_source_directory_structure():
    """
    Verify source directories created by T001b:
    src/generators, src/inference, src/analysis
    """
    root = Path(__file__).parent.parent.parent
    src_dirs = [
        "src/generators",
        "src/inference",
        "src/analysis",
    ]
    for d in src_dirs:
        path = root / d
        assert path.exists(), f"Missing required directory: {path}"
        assert path.is_dir(), f"Path is not a directory: {path}"


def test_test_directory_structure():
    """
    Verify test directories created by T001c:
    tests/unit, tests/integration
    """
    root = Path(__file__).parent.parent.parent
    test_dirs = [
        "tests/unit",
        "tests/integration",
    ]
    for d in test_dirs:
        path = root / d
        assert path.exists(), f"Missing required directory: {path}"
        assert path.is_dir(), f"Path is not a directory: {path}"
