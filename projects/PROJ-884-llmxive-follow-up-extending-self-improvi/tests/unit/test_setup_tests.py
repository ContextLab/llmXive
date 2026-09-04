"""
Unit tests for the setup_tests.py script functionality.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the project root to the path so we can import the setup module
# Assuming this test file is at tests/unit/test_setup_tests.py
# and setup_tests.py is at code/setup_tests.py
# Project root is parent of tests/ (which is same level as code/)
CURRENT_DIR = Path(__file__).resolve()
TESTS_DIR = CURRENT_DIR.parent
PROJECT_ROOT = TESTS_DIR.parent
CODE_DIR = PROJECT_ROOT / "code"

# Add code directory to path to import setup_tests
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from setup_tests import setup_tests_directories, TESTS_BASE, UNIT_DIR, INTEGRATION_DIR

class TestSetupTestsDirectories:
    """Tests for the setup_tests_directories function."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up and tear down test environment."""
        # Create a temporary directory to simulate project root for testing
        # This avoids modifying the actual project structure during tests
        self.temp_project_root = Path(tempfile.mkdtemp())
        self.temp_tests_base = self.temp_project_root / "tests"
        self.temp_unit_dir = self.temp_tests_base / "unit"
        self.temp_integration_dir = self.temp_tests_base / "integration"
        
        yield
        
        # Clean up temporary directory
        if self.temp_project_root.exists():
            shutil.rmtree(self.temp_project_root)

    def test_directories_created(self):
        """Test that the function creates the required directories."""
        # Temporarily override the module-level constants for testing
        # We'll test the logic by creating a modified version in the test
        import setup_tests
        
        # Save original values
        original_tests_base = setup_tests.TESTS_BASE
        original_unit_dir = setup_tests.UNIT_DIR
        original_integration_dir = setup_tests.INTEGRATION_DIR
        
        try:
            # Set to temporary paths
            setup_tests.TESTS_BASE = self.temp_tests_base
            setup_tests.UNIT_DIR = self.temp_unit_dir
            setup_tests.INTEGRATION_DIR = self.temp_integration_dir
            
            # Run the setup
            result = setup_tests.setup_tests_directories()
            
            # Verify result
            assert result is True, "setup_tests_directories should return True on success"
            assert self.temp_tests_base.exists(), "tests/ directory should exist"
            assert self.temp_unit_dir.exists(), "tests/unit/ directory should exist"
            assert self.temp_integration_dir.exists(), "tests/integration/ directory should exist"
            
        finally:
            # Restore original values
            setup_tests.TESTS_BASE = original_tests_base
            setup_tests.UNIT_DIR = original_unit_dir
            setup_tests.INTEGRATION_DIR = original_integration_dir

    def test_directories_writable(self):
        """Test that the created directories are writable."""
        import setup_tests
        
        original_tests_base = setup_tests.TESTS_BASE
        original_unit_dir = setup_tests.UNIT_DIR
        original_integration_dir = setup_tests.INTEGRATION_DIR
        
        try:
            setup_tests.TESTS_BASE = self.temp_tests_base
            setup_tests.UNIT_DIR = self.temp_unit_dir
            setup_tests.INTEGRATION_DIR = self.temp_integration_dir
            
            # Run setup
            setup_tests.setup_tests_directories()
            
            # Test writability of unit directory
            test_file_unit = self.temp_unit_dir / "test_write.txt"
            try:
                with open(test_file_unit, 'w') as f:
                    f.write("test content")
                assert test_file_unit.exists(), "Should be able to write to unit directory"
                with open(test_file_unit, 'r') as f:
                    assert f.read() == "test content", "Content should match"
            finally:
                if test_file_unit.exists():
                    test_file_unit.unlink()
            
            # Test writability of integration directory
            test_file_integration = self.temp_integration_dir / "test_write.txt"
            try:
                with open(test_file_integration, 'w') as f:
                    f.write("test content")
                assert test_file_integration.exists(), "Should be able to write to integration directory"
                with open(test_file_integration, 'r') as f:
                    assert f.read() == "test content", "Content should match"
            finally:
                if test_file_integration.exists():
                    test_file_integration.unlink()
                    
        finally:
            setup_tests.TESTS_BASE = original_tests_base
            setup_tests.UNIT_DIR = original_unit_dir
            setup_tests.INTEGRATION_DIR = original_integration_dir

    def test_existing_directories_handled(self):
        """Test that existing directories are handled correctly (exist_ok=True)."""
        import setup_tests
        
        original_tests_base = setup_tests.TESTS_BASE
        original_unit_dir = setup_tests.UNIT_DIR
        original_integration_dir = setup_tests.INTEGRATION_DIR
        
        try:
            setup_tests.TESTS_BASE = self.temp_tests_base
            setup_tests.UNIT_DIR = self.temp_unit_dir
            setup_tests.INTEGRATION_DIR = self.temp_integration_dir
            
            # Create directories manually first
            self.temp_tests_base.mkdir(parents=True, exist_ok=True)
            self.temp_unit_dir.mkdir(parents=True, exist_ok=True)
            self.temp_integration_dir.mkdir(parents=True, exist_ok=True)
            
            # Run setup - should not fail on existing directories
            result = setup_tests.setup_tests_directories()
            
            assert result is True, "Should succeed even if directories already exist"
            assert self.temp_tests_base.exists()
            assert self.temp_unit_dir.exists()
            assert self.temp_integration_dir.exists()
            
        finally:
            setup_tests.TESTS_BASE = original_tests_base
            setup_tests.UNIT_DIR = original_unit_dir
            setup_tests.INTEGRATION_DIR = original_integration_dir

    def test_directory_structure_correct(self):
        """Test that the directory structure matches expectations."""
        import setup_tests
        
        original_tests_base = setup_tests.TESTS_BASE
        original_unit_dir = setup_tests.UNIT_DIR
        original_integration_dir = setup_tests.INTEGRATION_DIR
        
        try:
            setup_tests.TESTS_BASE = self.temp_tests_base
            setup_tests.UNIT_DIR = self.temp_unit_dir
            setup_tests.INTEGRATION_DIR = self.temp_integration_dir
            
            setup_tests.setup_tests_directories()
            
            # Verify structure
            assert self.temp_unit_dir.is_dir(), "unit should be a directory"
            assert self.temp_integration_dir.is_dir(), "integration should be a directory"
            assert self.temp_unit_dir.parent == self.temp_tests_base, "unit should be direct child of tests"
            assert self.temp_integration_dir.parent == self.temp_tests_base, "integration should be direct child of tests"
            
        finally:
            setup_tests.TESTS_BASE = original_tests_base
            setup_tests.UNIT_DIR = original_unit_dir
            setup_tests.INTEGRATION_DIR = original_integration_dir
