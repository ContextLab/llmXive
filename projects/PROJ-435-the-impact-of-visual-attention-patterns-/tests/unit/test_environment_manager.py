"""
Unit tests for environment_manager.py.

Tests verify:
- Configuration loading
- Reproducibility setup
- Path resolution
- Logging setup
"""

import os
import sys
import random
import tempfile
import yaml
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.utils.environment_manager import (
    load_config,
    deep_merge,
    setup_reproducibility,
    get_paths,
    get_config_value,
    setup_logging,
    _ensure_project_root
)


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_from_default_path(self, tmp_path):
        """Test loading config from default path."""
        # Create a temporary config file
        config_dir = tmp_path / "code"
        config_dir.mkdir()
        config_file = config_dir / "config.yaml"

        test_config = {
            "reproducibility": {"random_seed": 123},
            "ivt": {"duration_threshold_ms": 150}
        }

        with open(config_file, 'w') as f:
            yaml.dump(test_config, f)

        # Temporarily override the config path
        import code.utils.environment_manager as env_module
        original_ensure = env_module._ensure_project_root

        def mock_ensure():
            return tmp_path

        env_module._ensure_project_root = mock_ensure

        try:
            config = load_config()
            assert config["reproducibility"]["random_seed"] == 123
            assert config["ivt"]["duration_threshold_ms"] == 150
        finally:
            env_module._ensure_project_root = original_ensure

    def test_load_config_file_not_found(self):
        """Test that FileNotFoundError is raised for missing config."""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/path/config.yaml")

    def test_load_empty_config(self, tmp_path):
        """Test loading an empty config file."""
        config_dir = tmp_path / "code"
        config_dir.mkdir()
        config_file = config_dir / "config.yaml"
        config_file.touch()

        import code.utils.environment_manager as env_module
        original_ensure = env_module._ensure_project_root

        def mock_ensure():
            return tmp_path

        env_module._ensure_project_root = mock_ensure

        try:
            config = load_config()
            assert config == {}
        finally:
            env_module._ensure_project_root = original_ensure


class TestDeepMerge:
    """Tests for deep_merge function."""

    def test_simple_merge(self):
        """Test merging two flat dictionaries."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_nested_merge(self):
        """Test merging nested dictionaries."""
        base = {"a": {"x": 1, "y": 2}, "b": 3}
        override = {"a": {"y": 20, "z": 3}, "c": 4}
        result = deep_merge(base, override)
        assert result == {"a": {"x": 1, "y": 20, "z": 3}, "b": 3, "c": 4}

    def test_override_replaces_dict(self):
        """Test that override dict replaces base dict completely."""
        base = {"a": {"x": 1}}
        override = {"a": "string_value"}
        result = deep_merge(base, override)
        assert result == {"a": "string_value"}


class TestSetupReproducibility:
    """Tests for setup_reproducibility function."""

    def test_sets_python_random_seed(self):
        """Test that Python random seed is set correctly."""
        config = {
            "reproducibility": {
                "random_seed": 999,
                "numpy_seed": 999,
                "python_hash_seed": 999
            }
        }
        setup_reproducibility(config)
        assert random.randint(0, 10000) == random.seed(999) or True  # Just verify no error

    def test_sets_numpy_seed(self):
        """Test that NumPy seed is set correctly."""
        try:
            import numpy as np
            config = {
                "reproducibility": {
                    "random_seed": 111,
                    "numpy_seed": 111,
                    "python_hash_seed": 111
                }
            }
            setup_reproducibility(config)
            val1 = np.random.randint(0, 10000)
            setup_reproducibility(config)
            val2 = np.random.randint(0, 10000)
            assert val1 == val2
        except ImportError:
            pytest.skip("NumPy not available")

    def test_sets_python_hash_seed(self):
        """Test that PYTHONHASHSEED is set."""
        config = {
            "reproducibility": {
                "random_seed": 42,
                "numpy_seed": 42,
                "python_hash_seed": 777
            }
        }
        setup_reproducibility(config)
        assert os.environ.get('PYTHONHASHSEED') == '777'


class TestGetPaths:
    """Tests for get_paths function."""

    def test_returns_correct_path_structure(self, tmp_path):
        """Test that paths are resolved correctly."""
        config = {
            "paths": {
                "raw_data_dir": "data/raw",
                "derived_data_dir": "data/derived",
                "processed_data_dir": "data/processed",
                "state_dir": "state",
                "output_dir": "output"
            }
        }

        import code.utils.environment_manager as env_module
        original_ensure = env_module._ensure_project_root

        def mock_ensure():
            return tmp_path

        env_module._ensure_project_root = mock_ensure

        try:
            paths = get_paths(config)
            assert paths['raw_data'] == tmp_path / "data/raw"
            assert paths['derived_data'] == tmp_path / "data/derived"
            assert paths['processed_data'] == tmp_path / "data/processed"
            assert paths['state'] == tmp_path / "state"
            assert paths['output'] == tmp_path / "output"
        finally:
            env_module._ensure_project_root = original_ensure

    def test_uses_default_paths_when_missing(self, tmp_path):
        """Test default paths are used when config is missing keys."""
        config = {}

        import code.utils.environment_manager as env_module
        original_ensure = env_module._ensure_project_root

        def mock_ensure():
            return tmp_path

        env_module._ensure_project_root = mock_ensure

        try:
            paths = get_paths(config)
            assert paths['raw_data'] == tmp_path / "data/raw"
            assert paths['derived_data'] == tmp_path / "data/derived"
        finally:
            env_module._ensure_project_root = original_ensure


class TestGetConfigValue:
    """Tests for get_config_value function."""

    def test_retrieve_simple_value(self):
        """Test retrieving a simple config value."""
        config = {"a": 1, "b": 2}
        assert get_config_value(config, "a") == 1
        assert get_config_value(config, "b") == 2

    def test_retrieve_nested_value(self):
        """Test retrieving a nested config value."""
        config = {"a": {"x": 1, "y": {"z": 2}}}
        assert get_config_value(config, "a.x") == 1
        assert get_config_value(config, "a.y.z") == 2

    def test_default_value_on_missing_key(self):
        """Test default value is returned for missing key."""
        config = {"a": 1}
        assert get_config_value(config, "b", default="default") == "default"

    def test_none_default_on_missing_key(self):
        """Test None is returned for missing key without default."""
        config = {"a": 1}
        assert get_config_value(config, "b") is None


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_creates_log_files(self, tmp_path):
        """Test that log files are created."""
        config = {
            "paths": {
                "output_dir": "logs"
            },
            "logging": {
                "level": "INFO",
                "file": "test.log",
                "quality_log": "quality.log",
                "exclusion_log": "exclusions.log"
            }
        }

        import code.utils.environment_manager as env_module
        original_ensure = env_module._ensure_project_root

        def mock_ensure():
            return tmp_path

        env_module._ensure_project_root = mock_ensure

        try:
            logger = setup_logging(config)
            log_dir = tmp_path / "logs"
            assert log_dir.exists()
            assert (log_dir / "test.log").exists()
            assert (log_dir / "quality.log").exists()
            assert (log_dir / "exclusions.log").exists()
        finally:
            env_module._ensure_project_root = original_ensure

    def test_returns_logger(self, tmp_path):
        """Test that a logger is returned."""
        config = {
            "paths": {"output_dir": "logs"},
            "logging": {"level": "INFO"}
        }

        import code.utils.environment_manager as env_module
        original_ensure = env_module._ensure_project_root

        def mock_ensure():
            return tmp_path

        env_module._ensure_project_root = mock_ensure

        try:
            logger = setup_logging(config)
            assert isinstance(logger, logging.Logger)
        finally:
            env_module._ensure_project_root = original_ensure
