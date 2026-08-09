"""
Unit tests for T006: Setup data directory structure.

Verifies that the directory creation logic works correctly and handles
edge cases like existing directories and permission issues.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to mock the imports from utils since we are testing in isolation
# or ensure the project structure allows importing.
# For this test, we assume the project root is the parent of 'tests'.

import sys
from pathlib import Path

# Add the code directory to the path if not already present
current_dir = Path(__file__).parent.parent.parent
code_dir = current_dir / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

# Mock the utils module dependencies to avoid circular imports or missing config issues
# in a pure unit test environment, we will test the logic directly or with mocks.

from unittest.mock import patch, MagicMock
from code.utils.logger import get_logger
from code.utils.config import get_project_root

# Import the function under test
# We need to import it dynamically to avoid issues if the module isn't fully set up yet
import importlib.util
spec = importlib.util.spec_from_file_location("setup_data_dirs", str(code_dir / "01_setup_data_dirs.py"))
setup_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup_module)

setup_data_directories = setup_module.setup_data_directories
REQUIRED_DIRS = setup_module.REQUIRED_DIRS

class TestSetupDataDirectories:
    """Tests for the setup_data_directories function."""

    def test_creates_missing_directories(self, tmp_path):
        """Test that the function creates directories that do not exist."""
        # Mock get_project_root to return our temp directory
        with patch('code.01_setup_data_dirs.get_project_root', return_value=str(tmp_path)):
            # Mock logger to avoid side effects
            with patch('code.01_setup_data_dirs.get_logger') as mock_logger:
                result = setup_data_directories()
                
                assert result is True
                
                # Verify all required directories were created
                for dir_name in REQUIRED_DIRS:
                    target_dir = tmp_path / dir_name
                    assert target_dir.exists()
                    assert target_dir.is_dir()

    def test_ignores_existing_directories(self, tmp_path):
        """Test that the function succeeds even if directories already exist."""
        # Pre-create the directories
        for dir_name in REQUIRED_DIRS:
            (tmp_path / dir_name).mkdir(parents=True, exist_ok=True)
        
        with patch('code.01_setup_data_dirs.get_project_root', return_value=str(tmp_path)):
            with patch('code.01_setup_data_dirs.get_logger') as mock_logger:
                result = setup_data_directories()
                
                assert result is True
                
                # Verify they are still there
                for dir_name in REQUIRED_DIRS:
                    target_dir = tmp_path / dir_name
                    assert target_dir.exists()

    def test_handles_writable_check(self, tmp_path):
        """Test that the function verifies writability."""
        with patch('code.01_setup_data_dirs.get_project_root', return_value=str(tmp_path)):
            with patch('code.01_setup_data_dirs.get_logger') as mock_logger:
                result = setup_data_directories()
                
                assert result is True

    def test_returns_false_on_unwritable_directory(self, tmp_path):
        """Test that the function returns False if a directory is not writable."""
        # Create a read-only directory to simulate a failure
        # Note: This might be tricky to test reliably across OS, but we can mock the behavior
        unwritable_dir = tmp_path / "data" / "raw" / "human_samples"
        unwritable_dir.mkdir(parents=True, exist_ok=True)
        
        # Make it read-only (only works if running as non-root)
        if os.geteuid() != 0:
            unwritable_dir.chmod(0o444)
            
            try:
                with patch('code.01_setup_data_dirs.get_project_root', return_value=str(tmp_path)):
                    with patch('code.01_setup_data_dirs.get_logger') as mock_logger:
                        result = setup_data_directories()
                        
                        # If we are root, the test might still pass, so we check the mock calls
                        # If not root, it should fail
                        if os.geteuid() != 0:
                            assert result is False
                            # Verify error was logged
                            error_calls = [call for call in mock_logger.return_value.error.call_args_list if "not writable" in str(call)]
                            assert len(error_calls) > 0
            finally:
                # Restore permissions for cleanup
                unwritable_dir.chmod(0o755)
        else:
            # If running as root, just verify the logic path exists
            with patch('code.01_setup_data_dirs.get_project_root', return_value=str(tmp_path)):
                with patch('code.01_setup_data_dirs.get_logger') as mock_logger:
                    result = setup_data_directories()
                    assert result is True
    
    def test_returns_false_on_project_root_failure(self):
        """Test that the function returns False if project root cannot be determined."""
        with patch('code.01_setup_data_dirs.get_project_root', return_value=None):
            with patch('code.01_setup_data_dirs.get_logger') as mock_logger:
                result = setup_data_directories()
                
                assert result is False
                mock_logger.return_value.error.assert_called_once()
                assert "Could not determine project root" in str(mock_logger.return_value.error.call_args)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])