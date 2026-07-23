import os
import tempfile
import shutil
import pytest
import sys

# Add the code directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'code'))

from utils import set_task_id
from create_results_dirs import ensure_results_directories

class TestCreateResultsDirs:
    def setup_method(self):
        """Setup a temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        # Mock the project root by changing the working directory logic implicitly
        # We will test the function by patching os.path operations if necessary,
        # but here we assume the function calculates paths relative to its own file.
        # To test effectively, we verify the logic creates the expected subdirectories.
        
    def teardown_method(self):
        """Clean up the temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_ensure_results_directories_creates_structure(self, monkeypatch):
        """Test that the function creates results/ and results/figures/."""
        # We need to simulate the environment where 'code' is inside a project root.
        # The function calculates paths relative to its own file location.
        # Since we are running from tests, we can't easily mock the file location.
        # Instead, we verify the logic by checking if the directories exist after running.
        # However, the function creates dirs in the actual repo structure.
        # To test in isolation without polluting the repo during unit tests,
        # we would ideally refactor to accept a base_path.
        # Given the constraint to extend existing files, we test the side effect
        # assuming the test runs in the project root context or we verify the logic.
        
        # Let's verify the logic by checking the function's behavior on a known path
        # by temporarily changing the working directory or mocking os.makedirs.
        
        created_dirs = []
        
        def mock_makedirs(path):
            created_dirs.append(path)
        
        def mock_exists(path):
            return False  # Pretend nothing exists so we force creation
        
        monkeypatch.setattr(os, 'makedirs', mock_makedirs)
        monkeypatch.setattr(os, 'exists', mock_exists)
        
        set_task_id("T009")
        
        # Call the function
        result = ensure_results_directories()
        
        # Assert it returned True
        assert result is True
        
        # Assert that two directories were attempted to be created
        # The function creates 'results' and 'results/figures'
        assert len(created_dirs) == 2
        
        # Verify the paths end with the expected names
        # The first should be the base 'results'
        # The second should be 'results/figures'
        # We check the last component of the path to be sure
        assert 'results' in created_dirs[0]
        assert 'figures' in created_dirs[1]

    def test_ensure_results_directories_handles_existing(self, monkeypatch):
        """Test that the function handles existing directories gracefully."""
        def mock_exists(path):
            return True  # Pretend everything exists
        
        created_dirs = []
        def mock_makedirs(path):
            created_dirs.append(path)
        
        monkeypatch.setattr(os, 'exists', mock_exists)
        monkeypatch.setattr(os, 'makedirs', mock_makedirs)
        
        set_task_id("T009")
        
        result = ensure_results_directories()
        
        assert result is True
        # makedirs should not be called if exists returns True
        assert len(created_dirs) == 0
        
    def test_ensure_results_directories_handles_os_error(self, monkeypatch):
        """Test that the function handles OSError gracefully."""
        def mock_exists(path):
            return False
        
        def mock_makedirs(path):
            raise OSError("Simulated OS Error")
        
        monkeypatch.setattr(os, 'exists', mock_exists)
        monkeypatch.setattr(os, 'makedirs', mock_makedirs)
        
        set_task_id("T009")
        
        result = ensure_results_directories()
        
        assert result is False