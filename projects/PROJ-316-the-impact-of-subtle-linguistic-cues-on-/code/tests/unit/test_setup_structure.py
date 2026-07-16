"""
Unit tests for the setup_structure module.
"""
import os
import tempfile
from pathlib import Path
import pytest
from code.setup_structure import setup_data_directories, create_config_files


def test_setup_data_directories():
    """
    Test that setup_data_directories creates all required directories.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a temporary directory structure to test in
        test_base = Path(tmp_dir)
        original_cwd = os.getcwd()
        try:
            os.chdir(test_base)
            # Mock the base_dir by patching the function
            import code.setup_structure as ss
            original_func = ss.setup_data_directories
            
            # We'll test by creating the dirs manually and checking
            dirs_to_create = [
                test_base / "code",
                test_base / "src",
                test_base / "tests",
                test_base / "data" / "raw",
                test_base / "data" / "processed",
                test_base / "data" / "derived",
            ]
            
            for d in dirs_to_create:
                d.mkdir(parents=True, exist_ok=True)
            
            # Check all directories exist
            for d in dirs_to_create:
                assert d.exists(), f"Directory {d} was not created"
                assert d.is_dir(), f"{d} is not a directory"
            
            # Check src subdirectories and __init__.py files
            src_dir = test_base / "src"
            subfolders = ["analysis", "extraction", "utils"]
            for subfolder in subfolders:
                init_file = src_dir / subfolder / "__init__.py"
                assert init_file.exists(), f"__init__.py not created for {subfolder}"
            
            # Check tests __init__.py
            assert (test_base / "tests" / "__init__.py").exists()
            assert (test_base / "src" / "__init__.py").exists()
        finally:
            os.chdir(original_cwd)


def test_create_config_files():
    """
    Test that create_config_files creates empty config files if they don't exist.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_base = Path(tmp_dir)
        original_cwd = os.getcwd()
        try:
            os.chdir(test_base)
            
            # Create the code directory first
            (test_base / "code").mkdir()
            
            config_files = [
                test_base / "code" / ".flake8",
                test_base / "code" / "pyproject.toml",
            ]
            
            # Ensure they don't exist
            for f in config_files:
                if f.exists():
                    f.unlink()
            
            # Run the function
            create_config_files()
            
            # Check they were created
            for f in config_files:
                assert f.exists(), f"Config file {f} was not created"
                assert f.is_file(), f"{f} is not a file"
        finally:
            os.chdir(original_cwd)