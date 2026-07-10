"""
Unit tests for code/utils/io.py
"""
import pytest
from pathlib import Path
import tempfile
import yaml

# Import the function under test
# We need to adjust the import path based on how tests are run.
# Assuming tests are run from the project root:
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.utils.io import load_simulation_config, get_config_value


def test_load_simulation_config_defaults():
    """Test loading the default configuration file."""
    # The default config path is code/simulation_config.yaml
    config_path = Path(__file__).resolve().parent.parent.parent / "code" / "simulation_config.yaml"
    config = load_simulation_config(config_path)

    assert isinstance(config, dict)
    assert "network_generation" in config
    assert "transport" in config
    assert "analysis" in config
    assert "runtime" in config


def test_load_simulation_config_custom_path():
    """Test loading a configuration from a custom path."""
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        sample_data = {
            "test_key": "test_value",
            "nested": {
                "value": 42
            }
        }
        yaml.dump(sample_data, f)
        temp_path = Path(f.name)

    try:
        config = load_simulation_config(temp_path)
        assert config["test_key"] == "test_value"
        assert config["nested"]["value"] == 42
    finally:
        temp_path.unlink()


def test_load_simulation_config_missing_file():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        load_simulation_config(Path("non_existent_file.yaml"))


def test_load_simulation_config_empty_file():
    """Test that ValueError is raised for empty file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("")
        temp_path = Path(f.name)

    try:
        with pytest.raises(ValueError):
            load_simulation_config(temp_path)
    finally:
        temp_path.unlink()


def test_get_config_value_found():
    """Test retrieving a value with a valid key path."""
    config = {
        "network_generation": {
            "base_cutoff_factor": 1.2
        },
        "transport": {
            "max_iterations": 1000
        }
    }

    assert get_config_value(config, "network_generation.base_cutoff_factor") == 1.2
    assert get_config_value(config, "transport.max_iterations") == 1000
    assert get_config_value(config, "network_generation") == {"base_cutoff_factor": 1.2}


def test_get_config_value_not_found():
    """Test retrieving a value with an invalid key path returns default."""
    config = {
        "network_generation": {
            "base_cutoff_factor": 1.2
        }
    }

    assert get_config_value(config, "network_generation.non_existent") is None
    assert get_config_value(config, "network_generation.non_existent", default=99) == 99
    assert get_config_value(config, "non_existent.top.level", default="default_val") == "default_val"