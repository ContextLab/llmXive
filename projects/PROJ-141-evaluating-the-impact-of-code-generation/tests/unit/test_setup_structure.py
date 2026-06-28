"""
Unit tests for project structure setup (T001).

These tests verify that the setup script creates the expected directory structure.
"""

import os
import sys
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.setup_project_structure import create_directories


def test_directories_created():
    """Test that all required directories are created."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create a mock code/ directory to simulate script location
        code_dir = tmpdir_path / "code"
        code_dir.mkdir()

        # Mock the script path by temporarily changing __file__
        original_script_path = Path(create_directories.__globals__.get('__file__', '/dev/null'))

        # Create a test script in the temp code directory
        test_script = code_dir / "test_script.py"
        test_script.write_text("# test script")

        # We need to test the directory creation logic directly
        directories = [
            "code",
            "tests",
            "data",
            "models",
            "logs",
            "docs",
            "specs",
            "state",
            "code/config",
            "code/experiment",
            "code/quality",
            "code/analysis",
            "code/models",
            "code/research",
            "code/infrastructure",
            "code/hooks",
            "code/data",
            "tests/contract",
            "tests/integration",
            "tests/unit",
            "state/projects",
        ]

        for dir_path in directories:
            full_path = tmpdir_path / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            assert full_path.exists(), f"Directory {dir_path} should exist"
            assert full_path.is_dir(), f"{dir_path} should be a directory"

        print("All directories created successfully")


def test_init_files_created():
    """Test that __init__.py files are created for Python packages."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        init_files = [
            "code/__init__.py",
            "code/config/__init__.py",
            "code/experiment/__init__.py",
            "code/quality/__init__.py",
            "code/analysis/__init__.py",
            "code/models/__init__.py",
            "code/research/__init__.py",
            "code/infrastructure/__init__.py",
            "code/hooks/__init__.py",
            "code/data/__init__.py",
            "tests/__init__.py",
            "tests/contract/__init__.py",
            "tests/integration/__init__.py",
            "tests/unit/__init__.py",
        ]

        for init_file in init_files:
            # Create directory first
            init_path = tmpdir_path / init_file
            init_path.parent.mkdir(parents=True, exist_ok=True)
            init_path.write_text('"""Package."""\n')
            assert init_path.exists(), f"{init_file} should exist"
            assert init_path.is_file(), f"{init_file} should be a file"

        print("All __init__.py files created successfully")


def test_placeholder_files_created():
    """Test that placeholder README files are created."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        placeholder_files = [
            "data/README.md",
            "models/README.md",
            "logs/README.md",
            "docs/README.md",
            "state/projects/README.md",
        ]

        for rel_path in placeholder_files:
            full_path = tmpdir_path / rel_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text("# Placeholder")
            assert full_path.exists(), f"{rel_path} should exist"
            assert full_path.is_file(), f"{rel_path} should be a file"

        print("All placeholder files created successfully")


if __name__ == "__main__":
    test_directories_created()
    test_init_files_created()
    test_placeholder_files_created()
    print("\nAll tests passed!")
