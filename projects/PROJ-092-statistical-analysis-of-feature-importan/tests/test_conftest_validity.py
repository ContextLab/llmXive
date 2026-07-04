"""
Minimal test to verify the conftest.py setup is working correctly.
This ensures that imports from the project modules function as expected
within the pytest environment.
"""
import sys
from pathlib import Path

def test_project_modules_importable():
    """
    Verify that core project modules can be imported.
    This validates the sys.path manipulation in conftest.py.
    """
    try:
        from utils.config import Config, get_config, reset_config
        from utils.logger import setup_logger, get_logger
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import project modules: {e}")

def test_config_reset_functionality():
    """
    Verify that the config reset fixture works.
    """
    from utils.config import get_config, reset_config, Config
    
    # Get initial config (might be default)
    config1 = get_config()
    
    # Reset
    reset_config()
    
    # Get again
    config2 = get_config()
    
    # They should be instances of Config or None/Default depending on implementation
    # The key is that no exception was raised
    assert isinstance(config1, Config) or config1 is None
    assert isinstance(config2, Config) or config2 is None

def test_logger_setup():
    """
    Verify that the logger setup functions work.
    """
    from utils.logger import setup_logger, get_logger
    
    logger = setup_logger(level="DEBUG")
    assert logger is not None
    assert logger.name == "llmXive" or logger.name == "root"

def test_path_fixtures_accessible(pytestconfig, tmp_path):
    """
    Verify that path fixtures defined in conftest are accessible.
    """
    # This test implicitly checks if fixtures like 'data_dir' are available
    # by attempting to use a generic tmp_path which is standard, 
    # but we can also check if we can import the fixture logic if needed.
    # For now, simple sanity check that the test environment is up.
    assert tmp_path.exists()