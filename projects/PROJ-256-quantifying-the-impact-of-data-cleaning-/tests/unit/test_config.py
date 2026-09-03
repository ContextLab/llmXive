import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.config import get_config, Config

def test_config_singleton():
    """Test that get_config returns the same instance."""
    config1 = get_config()
    config2 = get_config()
    assert config1 is config2

def test_config_get_method():
    """Test the get method of Config."""
    config = get_config()
    assert config.get("RANDOM_SEED") == 42
    assert config.get("BOOTSTRAP_ITERATIONS") == 1000
    assert config.get("NON_EXISTENT_KEY", "default") == "default"

def test_config_attribute_access():
    """Test that arbitrary attribute access doesn't raise errors."""
    config = get_config()
    # Should not raise
    _ = config.info("test")
    _ = config.debug("test")
    assert callable(config.some_random_method)

def test_config_paths():
    """Test that paths are correctly set."""
    config = get_config()
    assert config.get("RAW_DATA_PATH") is not None
    assert config.get("PROCESSED_DATA_PATH") is not None
    assert config.get("OUTPUT_PATH") is not None
