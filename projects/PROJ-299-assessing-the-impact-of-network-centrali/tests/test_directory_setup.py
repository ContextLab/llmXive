"""
Tests for directory structure setup.
"""
import os
import tempfile
from pathlib import Path
import pytest

# Import the setup functions
# Adjust import path based on actual project structure
# Assuming tests are at tests/ and code is at code/
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_directories import ensure_directory_structure, create_gitignore


def test_ensure_directory_structure():
    """Test that required directories are created."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        ensure_directory_structure(root)

        # Check required directories exist
        required_dirs = [
            "data/raw",
            "data/processed",
            "data/analysis",
            "outputs",
            "outputs/viz",
            "logs",
            "code/download",
            "code/preprocess",
            "code/centrality",
            "code/analysis",
            "code/viz",
            "code/config",
            "code/utils",
            "tests/unit",
            "tests/integration",
            "docs",
            "specs",
        ]

        for dir_path in required_dirs:
            full_path = root / dir_path
            assert full_path.exists(), f"Directory {dir_path} was not created"
            assert full_path.is_dir(), f"{dir_path} is not a directory"


def test_create_gitignore():
    """Test that .gitignore is created with correct content."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        create_gitignore(root)

        gitignore_path = root / ".gitignore"
        assert gitignore_path.exists(), ".gitignore file was not created"

        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for key patterns
        assert "data/raw/*.nii" in content, "Missing rule for .nii files"
        assert "data/processed/*.nii" in content, "Missing rule for processed .nii files"
        assert "outputs/*.pdf" in content, "Missing rule for PDF outputs"
        assert "logs/*.log" in content, "Missing rule for log files"
        assert "__pycache__/" in content, "Missing rule for __pycache__"
        assert ".env" in content, "Missing rule for .env files"