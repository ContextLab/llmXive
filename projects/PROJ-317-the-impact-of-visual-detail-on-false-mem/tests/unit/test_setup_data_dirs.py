import os
import shutil
import tempfile
from pathlib import Path
import pytest

# Add the code directory to the path for imports
sys_path_backup = __import__('sys').path.copy()
try:
    __import__('sys').path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
    from data.setup_data_dirs import setup_data_directories
    from config import get_config
finally:
    __import__('sys').path = sys_path_backup

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as the project root."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_setup_data_directories_creates_all_dirs(temp_project_root):
    """Test that setup_data_directories creates all required directories."""
    # Mock the config to use our temp directory
    original_get_config = None
    try:
        # We need to patch the get_config function or set the config globally
        # Since the function imports get_config, we'll rely on the environment
        # or patch it. For simplicity, let's assume the function respects
        # a PROJECT_ROOT env var or similar, but the current implementation
        # uses get_config().
        
        # To make this test robust, we will temporarily override the
        # config module's get_config if possible, or simply run the script
        # in a way that the config picks up the temp dir.
        # However, the simplest way given the current code structure is to
        # ensure the temp dir is the current working directory or passed correctly.
        # The current implementation uses `config.get("project_root") or Path.cwd()`.
        
        old_cwd = os.getcwd()
        os.chdir(temp_project_root)
        
        try:
            result = setup_data_directories()
            assert result is True, "setup_data_directories should return True on success"
            
            # Verify each directory exists
            required_dirs = [
                "data/stimuli",
                "data/responses",
                "data/processed",
                "data/stimuli_metadata",
                "data/ethics",
            ]
            
            for dir_name in required_dirs:
                dir_path = Path(temp_project_root) / dir_name
                assert dir_path.exists(), f"Directory {dir_name} was not created"
                assert dir_path.is_dir(), f"Path {dir_name} is not a directory"
        finally:
            os.chdir(old_cwd)
            
    except Exception as e:
        pytest.fail(f"Test failed with exception: {e}")

def test_setup_data_directories_idempotent(temp_project_root):
    """Test that running setup_data_directories twice does not cause errors."""
    old_cwd = os.getcwd()
    os.chdir(temp_project_root)
    
    try:
        # Run twice
        result1 = setup_data_directories()
        result2 = setup_data_directories()
        
        assert result1 is True
        assert result2 is True
        
        # Verify directories still exist
        required_dirs = [
            "data/stimuli",
            "data/responses",
            "data/processed",
            "data/stimuli_metadata",
            "data/ethics",
        ]
        
        for dir_name in required_dirs:
            dir_path = Path(temp_project_root) / dir_name
            assert dir_path.exists()
    finally:
        os.chdir(old_cwd)
