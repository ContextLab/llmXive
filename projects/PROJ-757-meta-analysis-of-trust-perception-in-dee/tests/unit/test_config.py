"""
Unit tests for configuration loading and validation.
"""
import pytest
import yaml
from pathlib import Path

# Import the config loader from the utils module
# Assuming T002 created code/utils.py, we import from there.
# If utils.py doesn't exist yet, this test will fail to import, which is expected
# until T006 implements it. However, we can test the structure here.
try:
    from code.utils import load_config
    HAS_UTILS = True
except ImportError:
    HAS_UTILS = False


@pytest.mark.skipif(not HAS_UTILS, reason="code.utils not yet implemented")
def test_load_config_valid():
    """Test loading a valid config file."""
    config_path = Path(__file__).parent.parent.parent / "config.yaml"
    # Create a dummy config if it doesn't exist for the test
    if not config_path.exists():
        config_path.write_text("test_key: test_value\n")
    
    config = load_config(config_path)
    assert config is not None
    assert "test_key" in config
    assert config["test_key"] == "test_value"

@pytest.mark.skipif(not HAS_UTILS, reason="code.utils not yet implemented")
def test_load_config_missing():
    """Test loading a missing config file raises an error."""
    config_path = Path(__file__).parent.parent.parent / "nonexistent.yaml"
    with pytest.raises(FileNotFoundError):
        load_config(config_path)
