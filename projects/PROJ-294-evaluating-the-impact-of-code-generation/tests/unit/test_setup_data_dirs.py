"""
Unit tests for code/setup_data_dirs.py
Verifies that the required data directories are created correctly.
"""
import os
import sys
import tempfile
import shutil
import unittest
from unittest.mock import patch, MagicMock

# Add the code directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

class TestSetupDataDirs(unittest.TestCase):
    
    def setUp(self):
        """Set up a temporary directory structure to simulate the project root."""
        self.temp_dir = tempfile.mkdtemp()
        self.code_dir = os.path.join(self.temp_dir, "code")
        os.makedirs(self.code_dir)
        
        # Mock the utils module to avoid dependency on the real project structure during test
        self.utils_patcher = patch('code.setup_data_dirs.get_logger')
        self.mock_get_logger = self.utils_patcher.start()
        self.mock_logger = MagicMock()
        self.mock_get_logger.return_value = self.mock_logger
        
        self.task_id_patcher = patch('code.setup_data_dirs.set_task_id')
        self.task_id_patcher.start()
        
        self.get_task_id_patcher = patch('code.setup_data_dirs.get_task_id', return_value="T008")
        self.get_task_id_patcher.start()

    def tearDown(self):
        """Clean up the temporary directory."""
        self.utils_patcher.stop()
        self.task_id_patcher.stop()
        self.get_task_id_patcher.stop()
        shutil.rmtree(self.temp_dir)

    @patch('code.setup_data_dirs.os.path.dirname')
    @patch('code.setup_data_dirs.os.path.abspath')
    def test_directories_created(self, mock_abspath, mock_dirname):
        """Test that the required directories are created."""
        # Mock the path detection to return our temp_dir
        mock_abspath.return_value = os.path.join(self.code_dir, "setup_data_dirs.py")
        mock_dirname.side_effect = lambda x: os.path.dirname(x) if isinstance(x, str) else os.path.dirname(os.path.join(self.temp_dir, "code"))
        
        # We need to manually set PROJECT_ROOT for the test logic since we can't easily mock the import
        # Instead, we will test the logic by importing and checking the behavior
        # For this specific test, we will assert the expected behavior by mocking os.makedirs
        
        with patch('code.setup_data_dirs.os.makedirs') as mock_makedirs:
            with patch('code.setup_data_dirs.os.path.exists', return_value=False):
                # Import the function to test
                from setup_data_dirs import create_directories
                
                # We need to patch the global variables inside the function scope
                # Since we can't easily do that, we will test the logic by checking the calls
                # This is a bit tricky because of the global PROJECT_ROOT definition
                
                # Let's instead test the main logic by mocking the environment
                import setup_data_dirs
                setup_data_dirs.PROJECT_ROOT = self.temp_dir
                
                result = create_directories()
                
                self.assertTrue(result)
                
                # Check that makedirs was called for the expected directories
                expected_calls = [
                    os.path.join(self.temp_dir, "data/raw"),
                    os.path.join(self.temp_dir, "data/generated"),
                    os.path.join(self.temp_dir, "data/analysis")
                ]
                
                # Verify os.makedirs was called with these paths
                calls = [call[0][0] for call in mock_makedirs.call_args_list]
                for expected in expected_calls:
                    self.assertIn(expected, calls)

    @patch('code.setup_data_dirs.os.path.dirname')
    @patch('code.setup_data_dirs.os.path.abspath')
    def test_directories_exist_already(self, mock_abspath, mock_dirname):
        """Test that existing directories are skipped."""
        mock_abspath.return_value = os.path.join(self.code_dir, "setup_data_dirs.py")
        mock_dirname.side_effect = lambda x: os.path.dirname(x) if isinstance(x, str) else os.path.dirname(os.path.join(self.temp_dir, "code"))
        
        import setup_data_dirs
        setup_data_dirs.PROJECT_ROOT = self.temp_dir
        
        # Create the directories first
        data_dirs = ["data/raw", "data/generated", "data/analysis"]
        for d in data_dirs:
            os.makedirs(os.path.join(self.temp_dir, d), exist_ok=True)
        
        with patch('code.setup_data_dirs.os.makedirs') as mock_makedirs:
            with patch('code.setup_data_dirs.os.path.exists', return_value=True):
                from setup_data_dirs import create_directories
                
                result = create_directories()
                
                self.assertTrue(result)
                
                # os.makedirs should not be called if directories already exist
                mock_makedirs.assert_not_called()
                
                # Check that logger.info was called for existing directories
                self.assertTrue(self.mock_logger.info.called)

    @patch('code.setup_data_dirs.os.path.dirname')
    @patch('code.setup_data_dirs.os.path.abspath')
    def test_makedirs_failure(self, mock_abspath, mock_dirname):
        """Test that the function returns False if makedirs fails."""
        mock_abspath.return_value = os.path.join(self.code_dir, "setup_data_dirs.py")
        mock_dirname.side_effect = lambda x: os.path.dirname(x) if isinstance(x, str) else os.path.dirname(os.path.join(self.temp_dir, "code"))
        
        import setup_data_dirs
        setup_data_dirs.PROJECT_ROOT = self.temp_dir
        
        with patch('code.setup_data_dirs.os.makedirs', side_effect=OSError("Permission denied")):
            with patch('code.setup_data_dirs.os.path.exists', return_value=False):
                from setup_data_dirs import create_directories
                
                result = create_directories()
                
                self.assertFalse(result)
                
                # Check that logger.error was called
                self.mock_logger.error.assert_called()

if __name__ == '__main__':
    unittest.main()