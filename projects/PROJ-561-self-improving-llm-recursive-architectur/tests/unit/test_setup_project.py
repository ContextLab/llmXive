import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the code directory to the path so we can import setup_project
# Note: In the actual project structure, this test file is in code/tests/unit/
# but the import logic in setup_project uses relative paths from the execution context.
# We will mock the file system operations to verify the logic without actually creating files on disk in the repo root.

class TestSetupProject(unittest.TestCase):
    
    def setUp(self):
        # Create a temporary directory to simulate the project root
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    @patch('setup_project.Path')
    def test_create_project_structure_creates_all_dirs(self, mock_path_class):
        """
        Verify that create_project_structure attempts to create all required directories.
        """
        # Mock the Path object and its methods
        mock_path_instance = MagicMock()
        mock_path_class.return_value = mock_path_instance
        
        # Mock the mkdir method to avoid actual file system changes during test
        # We need to track which paths are passed to mkdir
        created_paths = []
        
        def mock_mkdir(parents=True, exist_ok=True):
            # Capture the path this mock was called on
            created_paths.append(str(self))
        
        mock_path_instance.mkdir = mock_mkdir
        
        # We need to mock the specific paths that will be created
        # Since Path(".") returns the mock_path_instance, we need to handle the / operator
        # The / operator on a MagicMock returns a new MagicMock by default.
        # We need to ensure that when we call .mkdir() on these new mocks, we capture them.
        
        # Re-implementing the logic with better mocking:
        # The function does:
        # base_path = Path(".")
        # directories = [...]
        # for dir_path in directories:
        #     full_path = base_path / dir_path
        #     full_path.mkdir(...)
        
        # Let's mock the Path class to return a specific mock that records calls
        mock_base_path = MagicMock()
        mock_path_class.return_value = mock_base_path
        
        # Track mkdir calls
        mkdir_calls = []
        def track_mkdir(*args, **kwargs):
            mkdir_calls.append(str(self))
        
        mock_base_path.mkdir = track_mkdir
        
        # Mock the / operator to return a mock that also tracks mkdir
        # We need to create a class or use a factory for the child paths
        class MockPath(MagicMock):
            def mkdir(self, *args, **kwargs):
                mkdir_calls.append(str(self))
                return MagicMock()
        
        # Override __truediv__ to return MockPath instances
        def mock_truediv(other):
            child = MockPath()
            # We need to set the string representation to the path for debugging
            # But the actual string representation doesn't matter as much as the call tracking
            return child
        
        mock_base_path.__truediv__ = mock_truediv
        
        # Import and run the function
        # We need to reload the module to pick up the new mocks if it was already imported
        # But since we are patching at the function level, we can just call it
        import setup_project
        setup_project.create_project_structure()
        
        # Verify that mkdir was called 8 times (one for each directory)
        self.assertEqual(len(mkdir_calls), 8, f"Expected 8 directories, got {len(mkdir_calls)}")

    @patch('setup_project.Path')
    def test_create_project_structure_creates_init_files(self, mock_path_class):
        """
        Verify that __init__.py files are created in each directory.
        """
        mock_base_path = MagicMock()
        mock_path_class.return_value = mock_base_path
        
        init_files_created = []
        
        class MockPath(MagicMock):
            def mkdir(self, *args, **kwargs):
                return MagicMock()
            
            @property
            def exists(self):
                return False # Force creation
            
            def touch(self):
                init_files_created.append(str(self))
                return MagicMock()
        
        def mock_truediv(other):
            return MockPath()
        
        mock_base_path.__truediv__ = mock_truediv
        
        import setup_project
        setup_project.create_project_structure()
        
        # Verify that touch was called 8 times (one for each directory's __init__.py)
        # Note: The function creates __init__.py in 'code', 'data/raw', etc.
        # The loop iterates over 8 directories.
        self.assertEqual(len(init_files_created), 8, f"Expected 8 __init__.py files, got {len(init_files_created)}")

if __name__ == '__main__':
    unittest.main()