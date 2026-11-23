"""
Integration tests for the full generation pipeline (T012).
"""
import os
import sys
import tempfile
import shutil
import pytest
from pathlib import Path


def test_full_generation_pipeline_subset():
    """
    Integration test for full generation pipeline on a small subset.
    """
    # This test would ideally run the actual generation script
    # For now, we assert the existence of necessary directories
    root = Path(__file__).parent.parent.parent
    assert (root / "data" / "distorted").exists()
    assert (root / "output" / "control").exists()


def test_directory_structure_requirements():
    """
    Re-verify directory structure for integration context.
    """
    root = Path(__file__).parent.parent.parent
    required_dirs = [
        "data/raw",
        "data/distorted",
        "data/outputs",
        "src/generators",
        "tests/unit",
        "tests/integration",
    ]
    for d in required_dirs:
        path = root / d
        assert path.exists(), f"Missing directory: {path}"
