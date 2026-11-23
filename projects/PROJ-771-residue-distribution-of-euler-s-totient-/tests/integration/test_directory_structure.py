"""
Integration tests verifying the full directory structure setup.
This validates that T001a, T001b, T001c, and T001d work together.
"""
import os
import tempfile
from pathlib import Path
import pytest

# Add project root to path
import sys
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from setup_test_directories import setup_test_directories
from setup_data_directories import setup_data_directories
from setup_results_directories import setup_results_directories
from setup_directories import setup_directories

class TestFullDirectorySetup:
    """Integration test for all directory creation tasks."""

    def test_full_setup_creates_all_dirs(self, tmp_path):
        """Run all setup functions and verify the complete tree."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            # Create code dir so imports work
            (tmp_path / "code").mkdir()
            (tmp_path / "code" / "__init__.py").touch()
            
            # Run all setup tasks
            setup_directories() # T001a
            setup_data_directories() # T001b
            setup_results_directories() # T001c
            setup_test_directories() # T001d
            
            # Verify T001a
            assert (tmp_path / "code").exists()
            
            # Verify T001b
            assert (tmp_path / "data" / "raw").exists()
            assert (tmp_path / "data" / "processed").exists()
            
            # Verify T001c
            assert (tmp_path / "results" / "plots").exists()
            assert (tmp_path / "results" / "reports").exists()
            
            # Verify T001d
            assert (tmp_path / "tests" / "unit").exists()
            assert (tmp_path / "tests" / "integration").exists()
            
        finally:
            os.chdir(original_cwd)