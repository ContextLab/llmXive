import os
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from setup_directories import create_directories, verify_structure

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary project root for testing."""
    # Create a mock structure similar to the real project
    code_dir = tmp_path / "code"
    tests_dir = tmp_path / "tests"
    data_dir = tmp_path / "data"
    docs_dir = tmp_path / "docs"
    
    code_dir.mkdir()
    tests_dir.mkdir()
    data_dir.mkdir()
    docs_dir.mkdir()
    
    return tmp_path

def test_create_directories_creates_all_required_dirs(temp_project_root):
    """Test that create_directories creates all required directories."""
    # Change to temp root to simulate project root behavior
    original_cwd = os.getcwd()
    os.chdir(temp_project_root)
    
    try:
        # Mock the Path resolution to use temp root
        import setup_directories
        original_resolve = Path.resolve
        
        def mock_resolve(self, strict=False):
            if str(self) == "code/setup_directories.py":
                return temp_project_root / "code" / "setup_directories.py"
            return original_resolve(self, strict=strict)
        
        Path.resolve = mock_resolve
        
        created = create_directories()
        
        # Verify main directories exist
        assert (temp_project_root / "code").exists()
        assert (temp_project_root / "tests").exists()
        assert (temp_project_root / "data").exists()
        assert (temp_project_root / "docs").exists()
        
        # Verify data subdirectories exist
        assert (temp_project_root / "data" / "raw").exists()
        assert (temp_project_root / "data" / "processed").exists()
        assert (temp_project_root / "data" / "derived").exists()
        assert (temp_project_root / "data" / "config").exists()
        assert (temp_project_root / "data" / "logs").exists()
        
        # Verify test subdirectories exist
        assert (temp_project_root / "tests" / "unit").exists()
        assert (temp_project_root / "tests" / "integration").exists()
        
        Path.resolve = original_resolve
    finally:
        os.chdir(original_cwd)

def test_verify_structure_returns_true_when_all_exist(temp_project_root):
    """Test that verify_structure returns True when all directories exist."""
    # Create all required directories
    required_dirs = [
        "code", "tests", "data", "docs",
        "data/raw", "data/processed", "data/derived", "data/config", "data/logs",
        "tests/unit", "tests/integration"
    ]
    
    for dir_name in required_dirs:
        (temp_project_root / dir_name).mkdir(parents=True, exist_ok=True)
    
    original_cwd = os.getcwd()
    os.chdir(temp_project_root)
    
    try:
        import setup_directories
        original_resolve = Path.resolve
        
        def mock_resolve(self, strict=False):
            if str(self) == "code/setup_directories.py":
                return temp_project_root / "code" / "setup_directories.py"
            return original_resolve(self, strict=strict)
        
        Path.resolve = mock_resolve
        
        result = verify_structure()
        
        assert result is True
        
        Path.resolve = original_resolve
    finally:
        os.chdir(original_cwd)

def test_verify_structure_returns_false_when_missing(temp_project_root):
    """Test that verify_structure returns False when directories are missing."""
    # Only create some directories
    (temp_project_root / "code").mkdir()
    (temp_project_root / "data").mkdir()
    
    original_cwd = os.getcwd()
    os.chdir(temp_project_root)
    
    try:
        import setup_directories
        original_resolve = Path.resolve
        
        def mock_resolve(self, strict=False):
            if str(self) == "code/setup_directories.py":
                return temp_project_root / "code" / "setup_directories.py"
            return original_resolve(self, strict=strict)
        
        Path.resolve = mock_resolve
        
        result = verify_structure()
        
        assert result is False
        
        Path.resolve = original_resolve
    finally:
        os.chdir(original_cwd)
