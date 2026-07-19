import os
import sys
import tempfile
import shutil
import unittest
from unittest.mock import patch, MagicMock

# Add the code directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from setup_data_dirs import create_directories
from utils import set_task_id, get_logger

class TestDataDirectoryCreation(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory to simulate the project root."""
        self.temp_dir = tempfile.mkdtemp()
        # Create a mock 'data' directory inside the temp dir
        self.data_base = os.path.join(self.temp_dir, 'data')
        # Ensure the path structure matches what the script expects relative to the file
        # The script looks for 'data' relative to the project root (parent of 'code')
        # We will mock the path resolution to use our temp_dir as the project root
        
        # Mock the os.path.dirname logic to point to our temp_dir
        # The script calculates: os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # __file__ is tests/unit/test_setup_data_dirs.py
        # So it goes up two levels to the project root
        self.project_root = self.temp_dir

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.temp_dir)

    @patch('setup_data_dirs.os.path.dirname')
    @patch('setup_data_dirs.os.path.abspath')
    @patch('setup_data_dirs.os.makedirs')
    @patch('setup_data_dirs.os.path.exists')
    def test_creates_missing_directories(self, mock_exists, mock_makedirs, mock_abspath, mock_dirname):
        """Test that create_directories creates directories that do not exist."""
        # Setup mocks
        # Simulate that the directories do not exist
        mock_exists.side_effect = lambda path: False
        # Ensure abspath and dirname return values that lead to our temp_dir
        mock_abspath.return_value = os.path.join(self.project_root, 'code', 'setup_data_dirs.py')
        mock_dirname.side_effect = lambda path: os.path.dirname(path)
        
        # We need to override the base_dir calculation in the function
        # Since the function calculates it internally, we can't easily mock it without patching the module
        # Instead, let's patch the specific os.path operations to force the base_dir to self.data_base
        
        # Re-mock to force the logic
        mock_dirname.reset_mock()
        mock_abspath.reset_mock()
        mock_exists.reset_mock()
        mock_makedirs.reset_mock()

        # Mock abspath to return a path under our temp project root
        mock_abspath.return_value = os.path.join(self.project_root, 'code', 'setup_data_dirs.py')
        
        # Mock dirname to go up two levels
        def mock_dirname_side_effect(path):
            if path == os.path.join(self.project_root, 'code', 'setup_data_dirs.py'):
                return os.path.join(self.project_root, 'code')
            elif path == os.path.join(self.project_root, 'code'):
                return self.project_root
            return os.path.dirname(path)
        
        mock_dirname.side_effect = mock_dirname_side_effect
        
        # Simulate directories don't exist
        mock_exists.return_value = False

        # Call the function
        # Note: The function uses os.path.join(base_dir, 'raw') etc.
        # We need to ensure the base_dir resolves to self.data_base
        # The script: base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        # With our mocks:
        # abspath -> project_root/code/setup_data_dirs.py
        # dirname -> project_root/code
        # dirname -> project_root
        # join -> project_root/data
        
        result = create_directories()

        # Verify makedirs was called for all three subdirectories
        expected_calls = [
            unittest.mock.call(os.path.join(self.data_base, 'raw')),
            unittest.mock.call(os.path.join(self.data_base, 'generated')),
            unittest.mock.call(os.path.join(self.data_base, 'analysis'))
        ]
        
        # Check that makedirs was called with the correct arguments
        # Since we mocked exists to return False, makedirs should be called for all
        self.assertTrue(result)
        self.assertEqual(mock_makedirs.call_count, 3)
        
        # Verify the specific paths
        calls_args = [call[0][0] for call in mock_makedirs.call_args_list]
        self.assertIn(os.path.join(self.data_base, 'raw'), calls_args)
        self.assertIn(os.path.join(self.data_base, 'generated'), calls_args)
        self.assertIn(os.path.join(self.data_base, 'analysis'), calls_args)

    @patch('setup_data_dirs.os.path.exists')
    @patch('setup_data_dirs.os.makedirs')
    @patch('setup_data_dirs.os.path.dirname')
    @patch('setup_data_dirs.os.path.abspath')
    def test_skips_existing_directories(self, mock_abspath, mock_dirname, mock_makedirs, mock_exists):
        """Test that create_directories does not try to create directories that already exist."""
        # Setup mocks
        mock_exists.return_value = True
        mock_abspath.return_value = os.path.join(self.project_root, 'code', 'setup_data_dirs.py')
        mock_dirname.side_effect = lambda path: os.path.dirname(path)

        result = create_directories()

        # makedirs should not be called
        mock_makedirs.assert_not_called()
        self.assertTrue(result)

    @patch('setup_data_dirs.os.path.exists')
    @patch('setup_data_dirs.os.makedirs')
    @patch('setup_data_dirs.os.path.dirname')
    @patch('setup_data_dirs.os.path.abspath')
    def test_handles_creation_error(self, mock_abspath, mock_dirname, mock_makedirs, mock_exists):
        """Test that create_directories returns False if directory creation fails."""
        # Setup mocks
        mock_exists.return_value = False
        mock_abspath.return_value = os.path.join(self.project_root, 'code', 'setup_data_dirs.py')
        mock_dirname.side_effect = lambda path: os.path.dirname(path)
        mock_makedirs.side_effect = OSError("Permission denied")

        result = create_directories()

        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()