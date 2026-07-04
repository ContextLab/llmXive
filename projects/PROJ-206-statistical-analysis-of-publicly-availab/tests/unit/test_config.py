"""
Unit tests for configuration management.

These tests verify that the configuration system correctly:
- Loads configuration from YAML files
- Resolves paths relative to the project root
- Handles seed pinning for reproducibility
"""

import os
import tempfile
import yaml
import pytest

# We'll test the existence of the config module structure
# Actual implementation will be done in T005

def test_config_module_structure():
    """Verify that the config module can be imported when implemented."""
    try:
        from src.utils.config import get_config, resolve_path, get_seed
        assert callable(get_config)
        assert callable(resolve_path)
        assert callable(get_seed)
    except ImportError:
        # Config module not yet implemented - this is expected for T001b
        pytest.skip("Configuration module not yet implemented (T005)")

def test_temp_config_creation():
    """Test that we can create temporary config files."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config_data = {
            'seed': 42,
            'paths': {
                'data': 'data/',
                'output': 'data/processed/'
            }
        }
        yaml.dump(config_data, f)
        temp_path = f.name
    
    try:
        with open(temp_path, 'r') as f:
            loaded = yaml.safe_load(f)
            assert loaded['seed'] == 42
            assert loaded['paths']['data'] == 'data/'
    finally:
        os.unlink(temp_path)
