import os
import sys
import pytest
from pathlib import Path
import tempfile
import shutil

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from setup_project import create_directories, verify_directories

class TestSetupProject:
    @pytest.fixture
    def temp_project_root(self, tmp_path):
        """Create a temporary project structure for testing."""
        # Create a temporary directory that simulates project root
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        
        # Create code directory
        code_dir = project_root / "code"
        code_dir.mkdir()
        
        # Create the test file in code directory to match real structure
        test_file = code_dir / "setup_project_test.py"
        test_file.write_text("pass")
        
        return project_root

    def test_create_directories_creates_all(self, temp_project_root):
        """Test that create_directories creates all required folders."""
        # Mock logger
        class MockLogger:
            def info(self, msg): pass
            def debug(self, msg): pass
            def error(self, msg): pass
        
        logger = MockLogger()
        
        # Temporarily change working directory to simulate running from code/
        original_cwd = os.getcwd()
        code_dir = temp_project_root / "code"
        os.chdir(code_dir)
        
        try:
            # We need to import the module fresh to pick up the new path
            import importlib
            import setup_project
            importlib.reload(setup_project)
            
            created = setup_project.create_directories(logger)
            
            # Verify directories were created
            assert len(created) > 0
            
            # Check specific directories exist
            assert (temp_project_root / "data" / "raw").exists()
            assert (temp_project_root / "data" / "processed").exists()
            assert (temp_project_root / "data" / "reports").exists()
            assert (temp_project_root / "tests").exists()
            assert (temp_project_root / "state").exists()
        finally:
            os.chdir(original_cwd)

    def test_verify_directories_all_exist(self, temp_project_root):
        """Test verify_directories when all directories exist."""
        # Create directories first
        class MockLogger:
            def info(self, msg): pass
            def debug(self, msg): pass
            def error(self, msg): pass
        
        logger = MockLogger()
        original_cwd = os.getcwd()
        code_dir = temp_project_root / "code"
        os.chdir(code_dir)
        
        try:
            import importlib
            import setup_project
            importlib.reload(setup_project)
            
            setup_project.create_directories(logger)
            
            required = ["code", "data/raw", "data/processed", "data/reports", "tests", "state"]
            result = setup_project.verify_directories(required)
            
            assert result is True
        finally:
            os.chdir(original_cwd)

    def test_verify_directories_missing_one(self, temp_project_root):
        """Test verify_directories when a directory is missing."""
        required = ["code", "data/raw", "data/processed", "data/reports", "tests", "state"]
        
        # Don't create directories - they should be missing
        original_cwd = os.getcwd()
        code_dir = temp_project_root / "code"
        os.chdir(code_dir)
        
        try:
            import importlib
            import setup_project
            importlib.reload(setup_project)
            
            result = setup_project.verify_directories(required)
            
            assert result is False
        finally:
            os.chdir(original_cwd)
