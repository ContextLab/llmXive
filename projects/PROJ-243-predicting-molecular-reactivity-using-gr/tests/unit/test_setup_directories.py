import os
import pytest
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Mock config to use temporary directory
@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as project root."""
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    yield temp_dir
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_config(temp_project_root):
    """Return a mock config that uses the temp directory."""
    return {
        "seed": 42,
        "device": "cpu",
        "data_dirs": {
            "raw": os.path.join(temp_project_root, "data/raw"),
            "processed": os.path.join(temp_project_root, "data/processed"),
            "assets": os.path.join(temp_project_root, "data/assets")
        },
        "code_dir": os.path.join(temp_project_root, "code"),
        "artifacts_dir": os.path.join(temp_project_root, "artifacts"),
        "tests_dir": os.path.join(temp_project_root, "tests"),
        "log_dir": os.path.join(temp_project_root, "artifacts/logs"),
        "weight_dir": os.path.join(temp_project_root, "artifacts/weights"),
        "figure_dir": os.path.join(temp_project_root, "artifacts/figures"),
        "max_memory_gb": 4.0,
        "batch_size": 32,
        "learning_rate": 0.001,
        "epochs": 100,
        "early_stopping_patience": 5
    }

def test_create_directories_basic(temp_project_root):
    """Test that create_directories creates the specified directories."""
    # Import here to avoid config conflicts
    import sys
    sys.path.insert(0, os.path.join(temp_project_root, "code"))
    
    # We'll test the logic directly
    from setup_directories import create_directories
    import logging
    
    logger = logging.getLogger("test")
    logger.setLevel(logging.INFO)
    
    test_dirs = [
        "data/raw",
        "data/processed",
        "data/assets",
        "code",
        "artifacts",
        "tests"
    ]
    
    create_directories(test_dirs, logger)
    
    # Verify all directories were created
    for dir_path in test_dirs:
        assert os.path.exists(dir_path), f"Directory {dir_path} was not created"
        assert os.path.isdir(dir_path), f"{dir_path} is not a directory"

def test_create_directories_already_exist(temp_project_root):
    """Test that create_directories handles existing directories gracefully."""
    import sys
    sys.path.insert(0, os.path.join(temp_project_root, "code"))
    
    from setup_directories import create_directories
    import logging
    
    logger = logging.getLogger("test")
    logger.setLevel(logging.INFO)
    
    # Create a directory first
    os.makedirs("data/raw", exist_ok=True)
    
    # Try to create it again - should not raise
    create_directories(["data/raw"], logger)
    
    assert os.path.exists("data/raw")

def test_main_function_creates_all_dirs(temp_project_root):
    """Test that main() creates all required directories."""
    import sys
    sys.path.insert(0, os.path.join(temp_project_root, "code"))
    
    # Mock get_config to return our temp-based config
    with patch('setup_directories.get_config') as mock_get_config, \
         patch('setup_directories.ensure_directories') as mock_ensure:
        
        mock_get_config.return_value = {
            "data_dirs": {
                "raw": "data/raw",
                "processed": "data/processed",
                "assets": "data/assets"
            },
            "code_dir": "code",
            "artifacts_dir": "artifacts",
            "tests_dir": "tests",
            "log_dir": "artifacts/logs",
            "weight_dir": "artifacts/weights",
            "figure_dir": "artifacts/figures"
        }
        
        from setup_directories import main
        result = main()
        
        assert result == 0, "main() should return 0 on success"
        
        # Verify directories were created
        required_dirs = [
            "data/raw",
            "data/processed",
            "data/assets",
            "code",
            "artifacts",
            "tests",
            "artifacts/logs",
            "artifacts/weights",
            "artifacts/figures"
        ]
        
        for dir_path in required_dirs:
            assert os.path.exists(dir_path), f"Required directory {dir_path} was not created"

def test_config_ensure_directories():
    """Test that config.ensure_directories creates directories."""
    import sys
    import tempfile
    import shutil
    
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    
    try:
        # Reset config to avoid conflicts
        import code.config as config_module
        config_module._config = {}
        
        # Set up a test config
        test_config = {
            "data_dirs": {
                "raw": "test_data/raw",
                "processed": "test_data/processed"
            },
            "artifacts_dir": "test_artifacts",
            "log_dir": "test_artifacts/logs"
        }
        
        config_module.set_config(test_config)
        config_module.ensure_directories()
        
        # Verify creation
        assert os.path.exists("test_data/raw")
        assert os.path.exists("test_data/processed")
        assert os.path.exists("test_artifacts")
        assert os.path.exists("test_artifacts/logs")
        
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)
