"""
Integration test to verify the tests directory structure is correctly set up.
This test ensures that the setup process creates the expected hierarchy.
"""
import os
import sys
from pathlib import Path
import pytest

# Get the project root
CURRENT_FILE = Path(__file__).resolve()
TESTS_DIR = CURRENT_FILE.parent
PROJECT_ROOT = TESTS_DIR.parent
CODE_DIR = PROJECT_ROOT / "code"

# Add code directory to path to import setup module
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from setup_tests import TESTS_BASE, UNIT_DIR, INTEGRATION_DIR

class TestTestsDirectoryStructure:
    """Integration tests for the tests directory structure."""

    def test_tests_base_exists(self):
        """Test that the tests base directory exists."""
        assert TESTS_BASE.exists(), f"tests/ directory should exist at {TESTS_BASE}"
        assert TESTS_BASE.is_dir(), f"{TESTS_BASE} should be a directory"

    def test_unit_directory_exists(self):
        """Test that the unit subdirectory exists."""
        assert UNIT_DIR.exists(), f"tests/unit/ directory should exist at {UNIT_DIR}"
        assert UNIT_DIR.is_dir(), f"{UNIT_DIR} should be a directory"

    def test_integration_directory_exists(self):
        """Test that the integration subdirectory exists."""
        assert INTEGRATION_DIR.exists(), f"tests/integration/ directory should exist at {INTEGRATION_DIR}"
        assert INTEGRATION_DIR.is_dir(), f"{INTEGRATION_DIR} should be a directory"

    def test_directory_hierarchy_correct(self):
        """Test that the directory hierarchy is correctly structured."""
        # Verify parent-child relationships
        assert UNIT_DIR.parent == TESTS_BASE, "tests/unit/ should be a direct child of tests/"
        assert INTEGRATION_DIR.parent == TESTS_BASE, "tests/integration/ should be a direct child of tests/"
        
        # Verify relative paths
        assert UNIT_DIR.relative_to(TESTS_BASE) == Path("unit"), "unit should be at tests/unit"
        assert INTEGRATION_DIR.relative_to(TESTS_BASE) == Path("integration"), "integration should be at tests/integration"

    def test_directories_are_writable(self):
        """Test that all test directories are writable."""
        test_files = []
        
        try:
            # Test unit directory writability
            unit_test_file = UNIT_DIR / ".integration_test_writable"
            with open(unit_test_file, 'w') as f:
                f.write("integration test writable")
            test_files.append(unit_test_file)
            
            with open(unit_test_file, 'r') as f:
                content = f.read()
            assert content == "integration test writable", "Unit directory write/read successful"
            
            # Test integration directory writability
            integration_test_file = INTEGRATION_DIR / ".integration_test_writable"
            with open(integration_test_file, 'w') as f:
                f.write("integration test writable")
            test_files.append(integration_test_file)
            
            with open(integration_test_file, 'r') as f:
                content = f.read()
            assert content == "integration test writable", "Integration directory write/read successful"
            
        finally:
            # Clean up test files
            for test_file in test_files:
                if test_file.exists():
                    test_file.unlink()

    def test_directory_permissions(self):
        """Test that directories have appropriate permissions."""
        import stat
        
        # Check that directories have read, write, execute permissions for owner
        for dir_path in [TESTS_BASE, UNIT_DIR, INTEGRATION_DIR]:
            if os.name == 'posix':  # Unix/Linux/macOS
                mode = dir_path.stat().st_mode
                # Check owner permissions (read=4, write=2, execute=1)
                owner_perms = (mode >> 6) & 0o7
                assert owner_perms & stat.S_IRUSR, f"{dir_path} should be readable by owner"
                assert owner_perms & stat.S_IWUSR, f"{dir_path} should be writable by owner"
                assert owner_perms & stat.S_IXUSR, f"{dir_path} should be executable (traversable) by owner"
            else:  # Windows
                # On Windows, just check that we can access the directory
                assert os.access(dir_path, os.R_OK), f"{dir_path} should be readable"
                assert os.access(dir_path, os.W_OK), f"{dir_path} should be writable"
                assert os.access(dir_path, os.X_OK), f"{dir_path} should be traversable"