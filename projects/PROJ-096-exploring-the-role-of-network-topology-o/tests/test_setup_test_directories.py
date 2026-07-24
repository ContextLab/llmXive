import os
import sys
import pytest
from pathlib import Path

# Add the project root to the path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from setup_test_directories import create_test_directories

class TestSetupTestDirectories:
    """
    Tests for the test directory creation functionality (T001c).
    """

    def test_directories_exist_after_creation(self, tmp_path):
        """
        Verify that the create_test_directories function creates the required directories.
        
        This test uses a temporary directory to simulate the project root.
        """
        # Mock the project root by changing the working directory behavior
        # We patch the function to use our tmp_path instead of the real project root
        import setup_test_directories as module
        
        original_path = module.Path
        
        class MockPath:
            def __init__(self, path):
                self._path = path
            
            def resolve(self):
                return self
            
            @property
            def parent(self):
                return MockPath(self._path.parent)
            
            @property
            def parent(self):
                return MockPath(self._path.parent)
            
            def mkdir(self, parents=True, exist_ok=True):
                return self._path.mkdir(parents=parents, exist_ok=exist_ok)
            
            def __truediv__(self, other):
                return MockPath(self._path / other)
            
            def __str__(self):
                return str(self._path)
            
            def __fspath__(self):
                return str(self._path)
        
        # Temporarily replace Path with our mock
        module.Path = MockPath
        
        try:
            # Create test directories in the temp directory
            test_dir = tmp_path / "code"
            test_dir.mkdir()
            
            # Mock the script location
            original_script_path = module.Path(__file__)
            module.Path = lambda x: MockPath(test_dir)
            
            # Call the function
            result = create_test_directories()
            
            # Restore Path
            module.Path = original_path
            
            # Verify result
            assert result is True
            
            # Verify directories exist
            assert (tmp_path / "tests").exists()
            assert (tmp_path / "state" / "projects").exists()
            
        finally:
            # Restore original Path
            module.Path = original_path

    def test_directories_created_with_parents(self, tmp_path):
        """
        Verify that parent directories are created if they don't exist.
        """
        import setup_test_directories as module
        
        original_path = module.Path
        
        class MockPath:
            def __init__(self, path):
                self._path = path
            
            def resolve(self):
                return self
            
            @property
            def parent(self):
                return MockPath(self._path.parent)
            
            def mkdir(self, parents=True, exist_ok=True):
                return self._path.mkdir(parents=parents, exist_ok=exist_ok)
            
            def __truediv__(self, other):
                return MockPath(self._path / other)
            
            def __str__(self):
                return str(self._path)
            
            def __fspath__(self):
                return str(self._path)
        
        module.Path = MockPath
        
        try:
            test_dir = tmp_path / "code"
            test_dir.mkdir()
            
            module.Path = lambda x: MockPath(test_dir)
            
            result = create_test_directories()
            
            module.Path = original_path
            
            assert result is True
            assert (tmp_path / "state").exists()
            assert (tmp_path / "state" / "projects").exists()
            
        finally:
            module.Path = original_path

    def test_existing_directories_not_recreated(self, tmp_path):
        """
        Verify that existing directories are not recreated (exist_ok=True).
        """
        import setup_test_directories as module
        
        original_path = module.Path
        
        class MockPath:
            def __init__(self, path):
                self._path = path
                self.mkdir_called = False
            
            def resolve(self):
                return self
            
            @property
            def parent(self):
                return MockPath(self._path.parent)
            
            def mkdir(self, parents=True, exist_ok=True):
                if not self._path.exists():
                    self._path.mkdir(parents=parents, exist_ok=exist_ok)
                self.mkdir_called = True
            
            def __truediv__(self, other):
                return MockPath(self._path / other)
            
            def __str__(self):
                return str(self._path)
            
            def __fspath__(self):
                return str(self._path)
            
            def exists(self):
                return self._path.exists()
        
        module.Path = MockPath
        
        try:
            test_dir = tmp_path / "code"
            test_dir.mkdir()
            
            # Pre-create the directories
            (tmp_path / "tests").mkdir()
            (tmp_path / "state" / "projects").mkdir(parents=True)
            
            module.Path = lambda x: MockPath(test_dir)
            
            result = create_test_directories()
            
            module.Path = original_path
            
            assert result is True
            
        finally:
            module.Path = original_path
