import os
import tempfile
from pathlib import Path
import pytest
import yaml

# Ensure we can import from the project root
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.config import load_config, get_config, save_config_template

def test_save_config_template_creates_file():
    """Test that the template file is created with expected content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_config.yaml.template"
        save_config_template(output_path)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            content = f.read()
        
        # Check for key sections
        assert "api:" in content
        assert "random_seeds:" in content
        assert "constraints:" in content
        assert "paths:" in content
        assert "models:" in content
        assert "logging:" in content

def test_load_config_with_valid_file():
    """Test loading a valid config file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"
        
        # Create a minimal valid config
        config_data = {
            "api": {"keys": {"materials_project": "test_key"}},
            "random_seeds": {"global": 42},
            "constraints": {"time": {"max_pipeline_minutes": 360}}
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        loaded = load_config(config_path)
        
        assert loaded["api"]["keys"]["materials_project"] == "test_key"
        assert loaded["random_seeds"]["global"] == 42

def test_load_config_file_not_found():
    """Test that FileNotFoundError is raised for missing config."""
    with pytest.raises(FileNotFoundError):
        load_config(Path("/nonexistent/path/config.yaml"))

def test_get_config_key_exists():
    """Test retrieving an existing key."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"
        config_data = {"api": {"keys": {"materials_project": "test_key"}}}
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        # Temporarily override CONFIG_PATH for testing
        import code.config
        original_path = code.config.CONFIG_PATH
        code.config.CONFIG_PATH = config_path
        
        try:
            value = get_config("api.keys.materials_project")
            assert value == "test_key"
        finally:
            code.config.CONFIG_PATH = original_path

def test_get_config_key_missing_default():
    """Test retrieving a missing key with default value."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"
        config_data = {"api": {"keys": {}}}
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        import code.config
        original_path = code.config.CONFIG_PATH
        code.config.CONFIG_PATH = config_path
        
        try:
            value = get_config("api.keys.nonexistent", default="fallback")
            assert value == "fallback"
        finally:
            code.config.CONFIG_PATH = original_path

def test_get_config_full():
    """Test retrieving the full config dictionary."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"
        config_data = {"random_seeds": {"global": 42}}
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        import code.config
        original_path = code.config.CONFIG_PATH
        code.config.CONFIG_PATH = config_path
        
        try:
            config = get_config()
            assert isinstance(config, dict)
            assert config["random_seeds"]["global"] == 42
        finally:
            code.config.CONFIG_PATH = original_path