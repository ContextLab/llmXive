"""
Integration tests for the data flow pipeline.
"""
import pytest
import os
from pathlib import Path

def test_directory_structure_exists():
    """Verify that the required directory structure exists."""
    project_root = Path(__file__).parent.parent.parent
    
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/models",
        "tests/unit",
        "tests/integration",
        "specs"
    ]
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        assert full_path.exists(), f"Required directory missing: {full_path}"
        assert full_path.is_dir(), f"Path is not a directory: {full_path}"
