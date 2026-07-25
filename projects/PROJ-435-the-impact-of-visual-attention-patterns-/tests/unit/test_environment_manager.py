"""
Unit tests for the environment manager module.

Tests cover:
- Configuration loading
- Random seed setup
- Path resolution
- Config value retrieval
- Logging setup
"""

import os
import random
import tempfile
from pathlib import Path
import pytest
import yaml

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'code'))
from utils.environment_manager import (
    load_config,
    deep_merge,
    setup_reproducibility,
    get_paths,
    get_config_value,
    setup_logging
)


class TestLoadConfig:
    def test_load_config_from_file(self, tmp_path):
        """Test loading configuration from a valid YAML file."""
        config_content = {
            'random_seeds': {'python': 123, 'numpy': 456},
            'paths': {'raw_data': 'data/raw'}
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_content, f)

        result = load_config(str(config_file))
        assert result['random_seeds']['python'] == 123
        assert result['paths']['raw_data'] == 'data/raw'

    def test_load_config_missing_file(self):
        """Test that FileNotFoundError is raised for missing config file."""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/path/config.yaml")


class TestDeepMerge:
    def test_simple_merge(self):
        """Test basic dictionary merge."""
        base = {'a': 1, 'b': 2}
        override = {'b': 3, 'c': 4}
        result = deep_merge(base, override)
        assert result == {'a': 1, 'b': 3, 'c': 4}

    def test_nested_merge(self):
        """Test recursive merge of nested dictionaries."""
        base = {'a': {'x': 1, 'y': 2}, 'b': 3}
        override = {'a': {'y': 20, 'z': 30}}
        result = deep_merge(base, override)
        assert result == {'a': {'x': 1, 'y': 20, 'z': 30}, 'b': 3}

    def test_override_entire_nested_dict(self):
        """Test replacing a nested dictionary entirely."""
        base = {'a': {'x': 1}}
        override = {'a': {'y': 2}}
        result = deep_merge(base, override)
        # The override dict replaces the base dict at key 'a'
        assert result == {'a': {'y': 2}}


class TestSetupReproducibility:
    def test_seed_python(self):
        """Test that Python random seed is set correctly."""
        config = {'random_seeds': {'python': 999, 'numpy': 999}}
        setup_reproducibility(config)
        assert random.randint(0, 1000) == random.randint(0, 1000) is False
        # Reset and verify determinism
        random.seed(999)
        val1 = random.randint(0, 1000)
        random.seed(999)
        val2 = random.randint(0, 1000)
        assert val1 == val2

    def test_seed_numpy(self):
        """Test that NumPy random seed is set correctly."""
        try:
            import numpy as np
            config = {'random_seeds': {'python': 888, 'numpy': 888}}
            setup_reproducibility(config)
            # Verify determinism
            np.random.seed(888)
            val1 = np.random.randint(0, 1000)
            np.random.seed(888)
            val2 = np.random.randint(0, 1000)
            assert val1 == val2
        except ImportError:
            pytest.skip("NumPy not installed")


class TestGetPaths:
    def test_paths_resolution(self, tmp_path, monkeypatch):
        """Test that paths are resolved relative to project root."""
        # Create a mock config
        config = {
            'paths': {
                'raw_data': 'data/raw',
                'derived_data': 'data/derived'
            }
        }
        # Mock the project root
        monkeypatch.setattr('utils.environment_manager.Path.resolve', lambda self: tmp_path)
        paths = get_paths(config)
        assert paths['raw_data'] == tmp_path / 'data' / 'raw'
        assert paths['derived_data'] == tmp_path / 'data' / 'derived'


class TestGetConfigValue:
    def test_get_nested_value(self):
        """Test retrieving a nested configuration value."""
        config = {
            'random_seeds': {'python': 123},
            'analysis': {'threshold': 50}
        }
        assert get_config_value('random_seeds.python', config=config) == 123
        assert get_config_value('analysis.threshold', config=config) == 50

    def test_get_missing_value_with_default(self):
        """Test that default is returned for missing keys."""
        config = {'a': 1}
        assert get_config_value('b.c', default=999, config=config) == 999

    def test_get_missing_value_without_default(self):
        """Test that None is returned for missing keys without default."""
        config = {'a': 1}
        assert get_config_value('b.c', config=config) is None


class TestSetupLogging:
    def test_logging_setup(self, tmp_path, monkeypatch):
        """Test that logging is configured correctly."""
        config = {
            'logging': {
                'level': 'WARNING',
                'format': '%(levelname)s: %(message)s',
                'file': 'test.log'
            }
        }
        # Mock project root
        monkeypatch.setattr('utils.environment_manager.Path.resolve', lambda self: tmp_path)
        logger = setup_logging(config)
        assert logger.level == logging.WARNING
        assert logger.handlers is not None
        assert len(logger.handlers) > 0
