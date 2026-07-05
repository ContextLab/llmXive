"""
Tests for the configuration management module.
"""

import os
import random
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.utils.config import SocraticConfig, load_config_from_env, get_config, set_global_config


class TestSocraticConfig:
    """Test cases for the SocraticConfig dataclass."""

    def test_default_initialization(self):
        """Test that default values are set correctly."""
        config = SocraticConfig()
        assert config.seed == 42
        assert config.model_name == "microsoft/phi-1.5"
        assert config.batch_size == 2
        assert config.device == "cpu"
        assert config.quantization_bits == 4

    def test_path_resolution(self):
        """Test that relative paths are resolved to absolute paths."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            config = SocraticConfig(project_root=project_root)
            
            assert config.data_dir.is_absolute()
            assert str(config.data_dir).startswith(str(project_root))
            assert config.output_dir.is_absolute()

    def test_set_seed_determinism(self):
        """Test that set_seed produces deterministic results."""
        config = SocraticConfig(seed=123)
        
        config.set_seed()
        val1 = random.random()
        arr1 = np.random.rand(5)
        
        config.set_seed()
        val2 = random.random()
        arr2 = np.random.rand(5)
        
        assert val1 == val2
        np.testing.assert_array_equal(arr1, arr2)

    def test_to_dict_serialization(self):
        """Test that config can be converted to a dictionary."""
        config = SocraticConfig(seed=999, model_name="test-model")
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert config_dict["seed"] == 999
        assert config_dict["model_name"] == "test-model"
        assert "data_dir" in config_dict
        assert "output_dir" in config_dict

    def test_cpu_batch_size_constraint(self):
        """Test that batch size is constrained for CPU execution."""
        # This logic is usually enforced in the loader, but we check the config
        # creation allows setting it, and the loader logic (if any) handles it.
        # Here we just ensure the config accepts the value.
        config = SocraticConfig(device="cpu", batch_size=4)
        assert config.batch_size == 4
        # Note: The actual enforcement happens in load_config_from_env or training loop
        # based on the task requirements.


class TestLoadConfigFromEnv:
    """Test cases for environment variable loading."""

    def test_default_values(self):
        """Test that default values are used when env vars are missing."""
        # Clear relevant env vars
        with patch.dict(os.environ, {}, clear=False):
            for key in ["SROCATIC_SEED", "SROCATIC_MODEL_NAME", "SROCATIC_MAX_SEQ_LENGTH", "SROCATIC_BATCH_SIZE", "SROCATIC_DEVICE"]:
                if key in os.environ:
                    del os.environ[key]
            
            config = load_config_from_env()
            assert config.seed == 42
            assert config.model_name == "microsoft/phi-1.5"

    def test_custom_values(self):
        """Test that custom values are loaded from env vars."""
        env_vars = {
            "SROCATIC_SEED": "123",
            "SROCATIC_MODEL_NAME": "custom-model",
            "SROCATIC_MAX_SEQ_LENGTH": "1024",
            "SROCATIC_BATCH_SIZE": "1",
            "SROCATIC_DEVICE": "cpu"
        }
        
        with patch.dict(os.environ, env_vars):
            config = load_config_from_env()
            assert config.seed == 123
            assert config.model_name == "custom-model"
            assert config.max_seq_length == 1024
            assert config.batch_size == 1

    def test_cpu_batch_size_enforcement(self):
        """Test that batch size is forced to 2 for CPU even if env var is higher."""
        env_vars = {
            "SROCATIC_DEVICE": "cpu",
            "SROCATIC_BATCH_SIZE": "8"
        }
        
        with patch.dict(os.environ, env_vars):
            config = load_config_from_env()
            assert config.batch_size == 2


class TestGlobalConfig:
    """Test cases for global config management."""

    def test_get_config_initializes(self):
        """Test that get_config initializes the global config if None."""
        # Reset global config
        import src.utils.config as config_module
        original_config = config_module._global_config
        config_module._global_config = None
        
        try:
            config = get_config()
            assert config is not None
            assert isinstance(config, SocraticConfig)
        finally:
            config_module._global_config = original_config

    def test_set_global_config(self):
        """Test that set_global_config updates the global instance."""
        import src.utils.config as config_module
        
        custom_config = SocraticConfig(seed=555)
        set_global_config(custom_config)
        
        retrieved_config = get_config()
        assert retrieved_config.seed == 555