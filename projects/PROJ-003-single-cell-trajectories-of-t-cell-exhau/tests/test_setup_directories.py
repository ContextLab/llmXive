"""
Tests for the setup_directories module.

These tests verify that the directory structure is created correctly
and that the required subdirectories exist.
"""
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add the code directory to the path for imports
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from setup_directories import setup_directories


class TestSetupDirectories:
    """Test cases for the setup_directories function."""

    def test_creates_data_directories(self, tmp_path):
        """Test that data/raw, data/processed, and data/results are created."""
        # Temporarily change the working directory to tmp_path
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))
        
        try:
            # Create a mock code directory structure
            code_dir = tmp_path / "code"
            code_dir.mkdir()
            (code_dir / "setup_directories.py").write_text(
                Path(__file__).parent.parent / "code" / "setup_directories.py"
            )
            
            # Import and run the function
            import importlib.util
            spec = importlib.util.spec_from_file_location("setup_directories", code_dir / "setup_directories.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            module.setup_directories()
            
            # Verify directories exist
            assert (tmp_path / "data" / "raw").exists()
            assert (tmp_path / "data" / "processed").exists()
            assert (tmp_path / "data" / "results").exists()
        finally:
            os.chdir(original_cwd)

    def test_creates_test_directories(self, tmp_path):
        """Test that tests/unit and tests/integration are created."""
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))
        
        try:
            # Create a mock code directory structure
            code_dir = tmp_path / "code"
            code_dir.mkdir()
            (code_dir / "setup_directories.py").write_text(
                Path(__file__).parent.parent / "code" / "setup_directories.py"
            )
            
            import importlib.util
            spec = importlib.util.spec_from_file_location("setup_directories", code_dir / "setup_directories.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            module.setup_directories()
            
            # Verify directories exist
            assert (tmp_path / "tests" / "unit").exists()
            assert (tmp_path / "tests" / "integration").exists()
        finally:
            os.chdir(original_cwd)

    def test_creates_init_files(self, tmp_path):
        """Test that __init__.py files are created for test packages."""
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))
        
        try:
            # Create a mock code directory structure
            code_dir = tmp_path / "code"
            code_dir.mkdir()
            (code_dir / "setup_directories.py").write_text(
                Path(__file__).parent.parent / "code" / "setup_directories.py"
            )
            
            import importlib.util
            spec = importlib.util.spec_from_file_location("setup_directories", code_dir / "setup_directories.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            module.setup_directories()
            
            # Verify __init__.py files exist
            assert (tmp_path / "tests" / "unit" / "__init__.py").exists()
            assert (tmp_path / "tests" / "integration" / "__init__.py").exists()
        finally:
            os.chdir(original_cwd)

    def test_directories_are_writable(self, tmp_path):
        """Test that created directories are writable."""
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))
        
        try:
            # Create a mock code directory structure
            code_dir = tmp_path / "code"
            code_dir.mkdir()
            (code_dir / "setup_directories.py").write_text(
                Path(__file__).parent.parent / "code" / "setup_directories.py"
            )
            
            import importlib.util
            spec = importlib.util.spec_from_file_location("setup_directories", code_dir / "setup_directories.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            module.setup_directories()
            
            # Try to write a file to each directory
            test_content = "test"
            (tmp_path / "data" / "raw" / "test.txt").write_text(test_content)
            (tmp_path / "data" / "processed" / "test.txt").write_text(test_content)
            (tmp_path / "data" / "results" / "test.txt").write_text(test_content)
            (tmp_path / "tests" / "unit" / "test.txt").write_text(test_content)
            (tmp_path / "tests" / "integration" / "test.txt").write_text(test_content)
            
            # Verify files were created
            assert (tmp_path / "data" / "raw" / "test.txt").read_text() == test_content
            assert (tmp_path / "data" / "processed" / "test.txt").read_text() == test_content
            assert (tmp_path / "data" / "results" / "test.txt").read_text() == test_content
            assert (tmp_path / "tests" / "unit" / "test.txt").read_text() == test_content
            assert (tmp_path / "tests" / "integration" / "test.txt").read_text() == test_content
        finally:
            os.chdir(original_cwd)
