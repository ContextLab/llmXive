"""
Unit tests for the project setup script.
Verifies that the directory structure is created correctly.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Add the code directory to the path so we can import setup_project
# We need to adjust sys.path to find the module in the code folder
# Assuming this test runs from the project root
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from setup_project import main

def test_setup_creates_directories():
    """Test that the setup script creates the expected directory tree."""
    # Create a temporary directory to simulate the project root
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            
            # Run the main function
            # We need to monkeypatch the base_path in setup_project to use tmp_dir
            # Instead of the hardcoded projects/... path, we'll modify the logic slightly
            # or just verify the structure is created relative to the temp dir
            
            # To test properly, we'll import the function and patch the path logic
            # Since main() uses Path.cwd(), and we changed cwd to tmp_dir,
            # it will create projects/... inside tmp_dir
            
            result = main()
            assert result == 0, "Setup script should return 0"
            
            # Verify directories exist
            base_path = Path(tmp_dir) / "projects" / "PROJ-455-predicting-plant-stress-resilience"
            
            expected_dirs = [
                "code/data",
                "code/models",
                "code/analysis",
                "tests/unit",
                "tests/integration",
                "tests/contract",
                "tests/benchmark",
                "contracts",
                "data/raw",
                "data/processed",
                "data/results",
            ]
            
            for dir_name in expected_dirs:
                full_path = base_path / dir_name
                assert full_path.exists(), f"Directory {full_path} was not created"
                assert full_path.is_dir(), f"{full_path} is not a directory"
            
            # Verify __init__.py files exist for Python packages
            init_dirs = [
                "code/data",
                "code/models",
                "code/analysis",
                "tests/unit",
                "tests/integration",
                "tests/contract",
                "tests/benchmark",
            ]
            
            for dir_name in init_dirs:
                init_file = base_path / dir_name / "__init__.py"
                assert init_file.exists(), f"__init__.py missing in {dir_name}"
                
        finally:
            os.chdir(original_cwd)

def test_setup_idempotent():
    """Test that running setup again doesn't fail."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            
            # Run twice
            result1 = main()
            result2 = main()
            
            assert result1 == 0
            assert result2 == 0
            
        finally:
            os.chdir(original_cwd)