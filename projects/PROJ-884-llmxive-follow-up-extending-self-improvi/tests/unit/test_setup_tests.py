"""
Unit tests for the setup_tests module (T001c).
Verifies that the tests directory hierarchy is created correctly.
"""
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_tests import setup_tests_directories

class TestSetupTestsDirectories:
    """Tests for the setup_tests_directories function."""

    def test_creates_required_hierarchy(self, tmp_path):
        """Verify that the function creates tests/, tests/unit/, and tests/integration/."""
        created_dirs = setup_tests_directories(tmp_path)
        
        tests_root = tmp_path / "tests"
        unit_dir = tests_root / "unit"
        integration_dir = tests_root / "integration"
        
        assert len(created_dirs) == 3
        assert tests_root in created_dirs
        assert unit_dir in created_dirs
        assert integration_dir in created_dirs
        
        assert tests_root.exists()
        assert tests_root.is_dir()
        assert unit_dir.exists()
        assert unit_dir.is_dir()
        assert integration_dir.exists()
        assert integration_dir.is_dir()

    def test_directories_are_writable(self, tmp_path):
        """Verify that the created directories are writable."""
        created_dirs = setup_tests_directories(tmp_path)
        
        for dir_path in created_dirs:
            test_file = dir_path / "write_test_file.txt"
            try:
                with open(test_file, 'w') as f:
                    f.write("test content")
                assert test_file.exists()
                test_file.unlink()
            except IOError:
                pytest.fail(f"Directory {dir_path} is not writable")

    def test_handles_existing_directories(self, tmp_path):
        """Verify that the function handles existing directories gracefully."""
        # Create the hierarchy manually first
        (tmp_path / "tests" / "unit").mkdir(parents=True)
        (tmp_path / "tests" / "integration").mkdir(parents=True)
        
        # Should not raise an exception
        created_dirs = setup_tests_directories(tmp_path)
        
        assert len(created_dirs) == 3

    def test_raises_on_non_writable_parent(self, tmp_path):
        """Verify that the function raises an error if a parent directory is not writable."""
        # Create a read-only directory structure to simulate permission issues
        # Note: This test might be skipped on systems where the user has root privileges
        # or if the filesystem doesn't support permission changes (e.g., some CI environments)
        try:
            # Create a dummy structure
            dummy_dir = tmp_path / "readonly_test"
            dummy_dir.mkdir()
            dummy_dir.chmod(0o444)  # Read-only
            
            # This should fail because we can't write into the read-only directory
            # However, if running as root, this might not fail, so we skip in that case
            if os.geteuid() == 0:
                pytest.skip("Running as root, cannot test read-only permissions")
                
            setup_tests_directories(dummy_dir)
            pytest.fail("Expected OSError was not raised")
        except OSError:
            # Expected behavior
            pass
        except Exception:
            # If we get here, the test environment doesn't support permission changes
            pytest.skip("Filesystem does not support permission changes")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])