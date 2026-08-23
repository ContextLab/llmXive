"""
Unit tests for directory creation and verification (T001a-T001d).
"""
import os
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.setup_directories import ensure_directory_exists

class TestDirectoryCreation:
    """Tests for directory creation functionality."""
    
    def test_code_directory_exists(self, tmp_path):
        """Test that code/ directory can be created and verified."""
        # Change to temp directory to avoid polluting project root
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            result = ensure_directory_exists("code")
            assert result is True, "ensure_directory_exists should return True"
            assert os.path.isdir("code"), "code/ directory should exist on disk"
        finally:
            os.chdir(original_cwd)
    
    def test_data_directory_exists(self, tmp_path):
        """Test that data/ directory can be created and verified."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            result = ensure_directory_exists("data")
            assert result is True
            assert os.path.isdir("data")
        finally:
            os.chdir(original_cwd)
    
    def test_tests_directory_exists(self, tmp_path):
        """Test that tests/ directory can be created and verified."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            result = ensure_directory_exists("tests")
            assert result is True
            assert os.path.isdir("tests")
        finally:
            os.chdir(original_cwd)
    
    def test_docs_directory_exists(self, tmp_path):
        """Test that docs/ directory can be created and verified."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            result = ensure_directory_exists("docs")
            assert result is True
            assert os.path.isdir("docs")
        finally:
            os.chdir(original_cwd)
    
    def test_directory_persistence(self, tmp_path):
        """Test that directories persist after creation."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Create directory
            ensure_directory_exists("code")
            
            # Verify it exists again (simulating a fresh check)
            assert os.path.isdir("code")
            assert Path("code").exists()
        finally:
            os.chdir(original_cwd)