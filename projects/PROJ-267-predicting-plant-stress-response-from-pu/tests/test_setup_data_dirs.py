import os
import sys
import pytest
from pathlib import Path
import tempfile
import shutil

# Add the project root to the path so we can import code modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.setup_data_dirs import ensure_directory, main
from code.utils.logging_config import setup_logging

@pytest.fixture
def temp_test_dir():
    """Create a temporary directory for testing directory creation."""
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    yield temp_dir
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)

def test_ensure_directory_creates_new_dir(temp_test_dir):
    """Test that ensure_directory creates a new directory."""
    test_path = "data/test_new_dir"
    result = ensure_directory(test_path)
    
    assert result is True
    assert Path(test_path).exists()
    assert Path(test_path).is_dir()

def test_ensure_directory_existing_dir(temp_test_dir):
    """Test that ensure_directory returns True for existing directory."""
    test_path = "data/existing_dir"
    Path(test_path).mkdir(parents=True, exist_ok=True)
    
    result = ensure_directory(test_path)
    
    assert result is True
    assert Path(test_path).exists()

def test_ensure_directory_nested(temp_test_dir):
    """Test that ensure_directory creates nested directories."""
    test_path = "data/nested/deep/path"
    result = ensure_directory(test_path)
    
    assert result is True
    assert Path(test_path).exists()
    assert Path(test_path).is_dir()

def test_main_creates_required_dirs(temp_test_dir):
    """Test that main() creates the required data directories."""
    # Mock get_logger to avoid logging setup issues in tests
    import code.setup_data_dirs as sd
    original_logger = sd.get_logger
    
    # We just need to ensure the function runs without error
    # The actual logging is handled by the fixture
    try:
        main()
    except SystemExit as e:
        # SystemExit(0) is expected on success
        assert e.code == 0
    
    # Verify directories were created
    assert Path("data/raw").exists()
    assert Path("data/raw").is_dir()
    assert Path("data/processed").exists()
    assert Path("data/processed").is_dir()
