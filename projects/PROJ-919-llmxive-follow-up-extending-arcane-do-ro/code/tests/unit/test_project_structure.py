"""
Unit tests for project structure setup.
"""
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add the code directory to the path to import the setup script
code_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(code_dir))

import setup_project_structure


class TestProjectStructure:
    """Tests for the project structure setup functionality."""

    def test_setup_directories_creates_structure(self):
        """Verify that setup_directories creates the required folders."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Temporarily override PROJECT_ROOT for the test
            original_root = setup_project_structure.PROJECT_ROOT
            setup_project_structure.PROJECT_ROOT = Path(tmp_dir)

            try:
                created, skipped = setup_project_structure.setup_directories()
                
                # Verify at least some directories were created
                assert created > 0, "Expected at least one directory to be created"
                
                # Verify specific critical directories exist
                for dir_name in ["src", "tests", "data", "specs"]:
                    path = Path(tmp_dir) / dir_name
                    assert path.exists(), f"Directory {dir_name} should exist"
                    assert path.is_dir(), f"{dir_name} should be a directory"
                
                # Verify nested structures
                assert (Path(tmp_dir) / "data" / "raw").exists()
                assert (Path(tmp_dir) / "data" / "derived").exists()
                assert (Path(tmp_dir) / "specs" / "001-gene-regulation").exists()
                
            finally:
                # Restore original root
                setup_project_structure.PROJECT_ROOT = original_root

    def test_setup_directories_idempotent(self):
        """Verify that running setup twice doesn't fail and skips existing dirs."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            original_root = setup_project_structure.PROJECT_ROOT
            setup_project_structure.PROJECT_ROOT = Path(tmp_dir)

            try:
                # First run
                created_1, skipped_1 = setup_project_structure.setup_directories()
                
                # Second run
                created_2, skipped_2 = setup_project_structure.setup_directories()
                
                # Second run should create nothing
                assert created_2 == 0, "Second run should create no new directories"
                # Second run should skip all
                assert skipped_2 > 0, "Second run should skip existing directories"
                
            finally:
                setup_project_structure.PROJECT_ROOT = original_root

    def test_init_files_created(self):
        """Verify that __init__.py files are created in src and tests directories."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            original_root = setup_project_structure.PROJECT_ROOT
            setup_project_structure.PROJECT_ROOT = Path(tmp_dir)

            try:
                setup_project_structure.setup_directories()
                
                # Check for __init__.py in src subdirectories
                src_init = Path(tmp_dir) / "src" / "__init__.py"
                assert src_init.exists(), "__init__.py should exist in src"
                
                tests_init = Path(tmp_dir) / "tests" / "__init__.py"
                assert tests_init.exists(), "__init__.py should exist in tests"
                
                # Check nested __init__.py
                analysis_init = Path(tmp_dir) / "src" / "analysis" / "__init__.py"
                assert analysis_init.exists(), "__init__.py should exist in src/analysis"
                
            finally:
                setup_project_structure.PROJECT_ROOT = original_root