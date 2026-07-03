import pytest
import os
from pathlib import Path
import sys
from setup_directories import create_directories

class TestDirectoryCreation:
    """
    Tests for the directory creation logic in setup_directories.py.
    Verifies that all required project directories are created correctly.
    """

    def test_root_directories_exist(self, tmp_path):
        """Verify that root directories are created."""
        # Change to temp directory to avoid polluting actual project structure during test
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))
        
        try:
            # Mock the Path creation to work within tmp_path
            # We will check if the function creates the expected structure
            # by inspecting the logic or running it and checking existence
            
            # Since create_directories uses relative paths, we run it in tmp
            create_directories()
            
            # Check root directories
            assert (tmp_path / "code").exists()
            assert (tmp_path / "data").exists()
            assert (tmp_path / "results").exists()
            assert (tmp_path / "logs").exists()
        finally:
            os.chdir(original_cwd)

    def test_data_subdirectories_exist(self, tmp_path):
        """Verify that data subdirectories are created."""
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))
        
        try:
            create_directories()
            
            # Check specific data subdirectories required by T001c
            assert (tmp_path / "data" / "raw").exists()
            assert (tmp_path / "data" / "scaled").exists()
            assert (tmp_path / "data" / "config").exists()
            
            # Check additional data subdirectories
            assert (tmp_path / "data" / "synthetic").exists()
            assert (tmp_path / "data" / "metadata").exists()
        finally:
            os.chdir(original_cwd)

    def test_code_subdirectories_exist(self, tmp_path):
        """Verify that code subdirectories are created."""
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))
        
        try:
            create_directories()
            
            # Check code subdirectories
            assert (tmp_path / "code" / "simulation").exists()
            assert (tmp_path / "code" / "preprocessing").exists()
            assert (tmp_path / "code" / "analysis").exists()
            assert (tmp_path / "code" / "visualization").exists()
            assert (tmp_path / "code" / "tests").exists()
            assert (tmp_path / "code" / "utils").exists()
        finally:
            os.chdir(original_cwd)

    def test_results_subdirectories_exist(self, tmp_path):
        """Verify that results subdirectories are created."""
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))
        
        try:
            create_directories()
            
            # Check results subdirectories
            assert (tmp_path / "results" / "figures").exists()
            assert (tmp_path / "results" / "models").exists()
        finally:
            os.chdir(original_cwd)

    def test_scaled_subdirectories_exist(self, tmp_path):
        """Verify that specific scaled subdirectories are created."""
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))
        
        try:
            create_directories()
            
            # Check specific scaled subdirectories required by T001d (part of data setup)
            assert (tmp_path / "data" / "scaled" / "standardized").exists()
            assert (tmp_path / "data" / "scaled" / "minmax").exists()
            assert (tmp_path / "data" / "scaled" / "robust").exists()
        finally:
            os.chdir(original_cwd)