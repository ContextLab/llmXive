"""
Integration tests for the complete directory structure setup.

These tests verify that the entire directory hierarchy
is created correctly when running the setup scripts.
"""
import os
import tempfile
import pytest
from pathlib import Path
import subprocess
import sys

class TestDirectoryStructureIntegration:
    """Integration tests for directory structure creation."""

    def test_full_setup_creates_all_directories(self):
        """Test that running setup creates the complete directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            
            try:
                # Run the setup script
                result = subprocess.run(
                    [sys.executable, "-m", "setup_directories"],
                    cwd=os.path.join(tmpdir, "code"),
                    capture_output=True,
                    text=True
                )
                
                # Check that setup completed
                assert result.returncode == 0, f"Setup failed: {result.stderr}"
                
                # Verify all required directories exist
                required_dirs = [
                    "data/raw",
                    "data/processed",
                    "data/output",
                    "code/utils",
                    "code/models",
                    "code/tests",
                    "tests/unit",
                    "tests/integration",
                    "specs"
                ]
                
                for dir_path in required_dirs:
                    assert os.path.exists(dir_path), f"Missing directory: {dir_path}"
            finally:
                os.chdir(original_cwd)

    def test_specs_placeholder_files_created(self):
        """Test that specs directory contains placeholder files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            
            try:
                # Run setup
                subprocess.run(
                    [sys.executable, "-m", "run_specs_setup"],
                    cwd=os.path.join(tmpdir, "code"),
                    capture_output=True
                )
                
                # Check for expected placeholder files
                expected_files = [
                    "specs/001-assessing-the-impact-of-sample-size-on-t/plan.md",
                    "specs/001-assessing-the-impact-of-sample-size-on-t/spec.md",
                    "specs/001-assessing-the-impact-of-sample-size-on-t/research.md",
                    "specs/001-assessing-the-impact-of-sample-size-on-t/data-model.md",
                    "specs/001-assessing-the-impact-of-sample-size-on-t/contracts/endpoints.md"
                ]
                
                for file_path in expected_files:
                    assert os.path.exists(file_path), f"Missing file: {file_path}"
            finally:
                os.chdir(original_cwd)

    def test_directory_structure_is_valid_python_package(self):
        """Test that created directories can be used as Python packages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            
            try:
                # Run setup
                subprocess.run(
                    [sys.executable, "-m", "setup_directories"],
                    cwd=os.path.join(tmpdir, "code"),
                    capture_output=True
                )
                
                # Create __init__.py files
                init_files = [
                    "tests/__init__.py",
                    "tests/unit/__init__.py",
                    "tests/integration/__init__.py",
                    "code/__init__.py",
                    "code/utils/__init__.py",
                    "code/models/__init__.py"
                ]
                
                for init_file in init_files:
                    with open(init_file, 'w') as f:
                        f.write("# Package initialization\n")
                
                # Try to import from the packages
                sys.path.insert(0, tmpdir)
                try:
                    import tests
                    import tests.unit
                    import tests.integration
                    assert True
                finally:
                    sys.path.remove(tmpdir)
            finally:
                os.chdir(original_cwd)
