"""
Tests for the configuration loader.
"""
import os
import tempfile
import pytest
from pathlib import Path
import yaml
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.config.loader import load_config

def test_load_default_config():
    """Test loading the default settings.yaml file."""
    # Ensure the default file exists
    config_path = Path(__file__).parent.parent.parent / "code" / "config" / "settings.yaml"
    assert config_path.exists(), "Default settings.yaml must exist for this test"
    
    config = load_config()
    
    assert isinstance(config, dict)
    assert 'seed' in config
    assert 'timeout_hours' in config
    assert config['timeout_hours'] == 5.5
    assert 'training' in config
    assert 'data' in config
    
def test_load_custom_config():
    """Test loading a custom config file."""
    custom_config = {
        'seed': 123,
        'timeout_hours': 2.0,
        'training': {'batch_size': 16},
        'data': {'datasets': []}
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(custom_config, f)
        temp_path = f.name
        
    try:
        config = load_config(temp_path)
        assert config['seed'] == 123
        assert config['timeout_hours'] == 2.0
    finally:
        os.unlink(temp_path)
        
def test_load_missing_config():
    """Test that loading a missing file raises an error."""
    with pytest.raises(FileNotFoundError):
        load_config("/non/existent/path/config.yaml")
        
def test_load_invalid_yaml():
    """Test that loading invalid YAML raises an error."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("invalid: yaml: content: [")
        temp_path = f.name
        
    try:
        with pytest.raises(yaml.YAMLError):
            load_config(temp_path)
    finally:
        os.unlink(temp_path)
        
def test_config_structure():
    """Test that the default config has the expected structure."""
    config = load_config()
    
    # Check nested structures
    assert 'model_name' in config['training']
    assert 'min_traces_per_prompt' in config['data']
    assert 'paths' in config
    assert 'logging' in config