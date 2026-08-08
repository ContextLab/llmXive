import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the code directory to the path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from create_t001b_directories import create_t001b_directories
from verify_t001b_structure import verify_t001b_structure

class TestCreateT001bDirectories:
    
    def setup_method(self):
        """Create a temporary directory for testing."""
        self.temp_base = tempfile.mkdtemp()
        self.test_project_root = Path(self.temp_base) / "projects" / "PROJ-951-llmxive-follow-up-extending-physisforcin" / "code"
        self.test_project_root.mkdir(parents=True)
    
    def teardown_method(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.temp_base, ignore_errors=True)
    
    def test_directories_created(self):
        """Test that src/, tests/, and data/ are created."""
        result = create_t001b_directories(self.test_project_root)
        
        assert result is True, "Directory creation should return True on success"
        
        src_path = self.test_project_root / "src"
        tests_path = self.test_project_root / "tests"
        data_path = self.test_project_root / "data"
        
        assert src_path.exists(), "src directory should exist"
        assert src_path.is_dir(), "src should be a directory"
        
        assert tests_path.exists(), "tests directory should exist"
        assert tests_path.is_dir(), "tests should be a directory"
        
        assert data_path.exists(), "data directory should exist"
        assert data_path.is_dir(), "data should be a directory"
    
    def test_verify_structure_passes(self):
        """Test that verification passes after creation."""
        # First create the directories
        create_t001b_directories(self.test_project_root)
        
        # Then verify
        result = verify_t001b_structure(self.test_project_root)
        
        assert result is True, "Verification should pass after successful creation"
    
    def test_verify_structure_fails_if_missing(self):
        """Test that verification fails if a directory is missing."""
        # Create only 'src'
        (self.test_project_root / "src").mkdir()
        
        result = verify_t001b_structure(self.test_project_root)
        
        assert result is False, "Verification should fail if directories are missing"
    
    def test_idempotent_creation(self):
        """Test that running creation twice doesn't cause errors."""
        result1 = create_t001b_directories(self.test_project_root)
        result2 = create_t001b_directories(self.test_project_root)
        
        assert result1 is True
        assert result2 is True