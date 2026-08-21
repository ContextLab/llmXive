"""
Unit tests for the setup_project module.
"""
import os
import tempfile
from pathlib import Path
import pytest

# Import the module to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.setup_project import setup_directories


def test_setup_directories_creates_all_folders():
    """Test that setup_directories creates all required directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a mock code directory structure
        code_dir = Path(tmpdir) / "code"
        code_dir.mkdir()
        
        # Mock the __file__ path by temporarily changing the module's __file__
        import code.setup_project as setup_module
        original_file = setup_module.__file__
        setup_module.__file__ = str(code_dir / "setup_project.py")
        
        try:
            # Run the setup
            result = setup_directories()
            
            # Verify all directories were created
            expected_dirs = [
                "code/data",
                "code/features",
                "code/models",
                "code/analysis",
                "data",
                "models",
                "reports",
                "tests/unit",
                "tests/contract",
                "tests/integration",
            ]
            
            for dir_path in expected_dirs:
                full_path = Path(tmpdir) / dir_path
                assert full_path.exists(), f"Directory {full_path} was not created"
                assert full_path.is_dir(), f"{full_path} is not a directory"
            
            assert result is True
        finally:
            # Restore original __file__
            setup_module.__file__ = original_file


def test_setup_directories_idempotent():
    """Test that running setup_directories multiple times doesn't cause errors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        code_dir = Path(tmpdir) / "code"
        code_dir.mkdir()
        
        import code.setup_project as setup_module
        original_file = setup_module.__file__
        setup_module.__file__ = str(code_dir / "setup_project.py")
        
        try:
            # Run setup twice
            setup_directories()
            setup_directories()
            
            # Verify directories still exist
            expected_dirs = ["data", "models", "reports"]
            for dir_path in expected_dirs:
                full_path = Path(tmpdir) / dir_path
                assert full_path.exists()
        finally:
            setup_module.__file__ = original_file