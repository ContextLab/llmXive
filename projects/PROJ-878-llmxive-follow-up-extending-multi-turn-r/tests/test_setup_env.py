"""
Tests for environment configuration setup.
"""
import os
import pytest
import random
import numpy as np
import torch

from code.setup_env import (
    configure_environment,
    get_environment_config,
    apply_seed,
    DEFAULT_SEED,
    DEFAULT_MODEL_PATH,
    DEFAULT_DEVICE,
    DEFAULT_MAX_TURNS,
    DEFAULT_EXTENDED_MAX_TURNS,
    DEFAULT_DATA_PATH_RAW,
    DEFAULT_DATA_PATH_PROCESSED,
    DEFAULT_RESULTS_PATH
)

class TestEnvironmentConfiguration:
    """Tests for environment variable configuration."""

    def setup_method(self):
        """Clean up environment variables before each test."""
        # Store original values
        self.original_seed = os.environ.get("LLMXIVE_SEED")
        self.original_model = os.environ.get("LLMXIVE_MODEL_PATH")
        self.original_device = os.environ.get("LLMXIVE_DEVICE")
        self.original_max_turns = os.environ.get("LLMXIVE_MAX_TURNS")
        self.original_extended_turns = os.environ.get("LLMXIVE_EXTENDED_MAX_TURNS")
        self.original_data_raw = os.environ.get("LLMXIVE_DATA_RAW")
        self.original_data_processed = os.environ.get("LLMXIVE_DATA_PROCESSED")
        self.original_results = os.environ.get("LLMXIVE_RESULTS_PATH")
        
        # Remove all llmXive environment variables
        for key in [
            "LLMXIVE_SEED", "LLMXIVE_MODEL_PATH", "LLMXIVE_DEVICE",
            "LLMXIVE_MAX_TURNS", "LLMXIVE_EXTENDED_MAX_TURNS",
            "LLMXIVE_DATA_RAW", "LLMXIVE_DATA_PROCESSED", "LLMXIVE_RESULTS_PATH"
        ]:
            os.environ.pop(key, None)

    def teardown_method(self):
        """Restore original environment variables after each test."""
        # Restore original values
        if self.original_seed is not None:
            os.environ["LLMXIVE_SEED"] = self.original_seed
        else:
            os.environ.pop("LLMXIVE_SEED", None)
            
        if self.original_model is not None:
            os.environ["LLMXIVE_MODEL_PATH"] = self.original_model
        else:
            os.environ.pop("LLMXIVE_MODEL_PATH", None)
            
        if self.original_device is not None:
            os.environ["LLMXIVE_DEVICE"] = self.original_device
        else:
            os.environ.pop("LLMXIVE_DEVICE", None)
            
        if self.original_max_turns is not None:
            os.environ["LLMXIVE_MAX_TURNS"] = self.original_max_turns
        else:
            os.environ.pop("LLMXIVE_MAX_TURNS", None)
            
        if self.original_extended_turns is not None:
            os.environ["LLMXIVE_EXTENDED_MAX_TURNS"] = self.original_extended_turns
        else:
            os.environ.pop("LLMXIVE_EXTENDED_MAX_TURNS", None)
            
        if self.original_data_raw is not None:
            os.environ["LLMXIVE_DATA_RAW"] = self.original_data_raw
        else:
            os.environ.pop("LLMXIVE_DATA_RAW", None)
            
        if self.original_data_processed is not None:
            os.environ["LLMXIVE_DATA_PROCESSED"] = self.original_data_processed
        else:
            os.environ.pop("LLMXIVE_DATA_PROCESSED", None)
            
        if self.original_results is not None:
            os.environ["LLMXIVE_RESULTS_PATH"] = self.original_results
        else:
            os.environ.pop("LLMXIVE_RESULTS_PATH", None)

    def test_configure_environment_sets_defaults(self):
        """Test that configure_environment sets default values when none are provided."""
        config = configure_environment()
        
        assert config["seed"] == DEFAULT_SEED
        assert config["model_path"] == DEFAULT_MODEL_PATH
        assert config["device"] == DEFAULT_DEVICE
        assert config["max_turns"] == DEFAULT_MAX_TURNS
        assert config["extended_max_turns"] == DEFAULT_EXTENDED_MAX_TURNS
        assert config["data_raw"] == DEFAULT_DATA_PATH_RAW
        assert config["data_processed"] == DEFAULT_DATA_PATH_PROCESSED
        assert config["results_path"] == DEFAULT_RESULTS_PATH

    def test_configure_environment_accepts_custom_values(self):
        """Test that configure_environment accepts and sets custom values."""
        custom_config = {
            "seed": 123,
            "model_path": "test/model",
            "device": "cuda"
        }
        
        config = configure_environment(
            seed=custom_config["seed"],
            model_path=custom_config["model_path"],
            device=custom_config["device"]
        )
        
        assert config["seed"] == custom_config["seed"]
        assert config["model_path"] == custom_config["model_path"]
        assert config["device"] == custom_config["device"]

    def test_environment_variables_are_set(self):
        """Test that configure_environment sets the correct environment variables."""
        configure_environment(seed=456, model_path="custom/model", device="cpu")
        
        assert os.environ["LLMXIVE_SEED"] == "456"
        assert os.environ["LLMXIVE_MODEL_PATH"] == "custom/model"
        assert os.environ["LLMXIVE_DEVICE"] == "cpu"

    def test_get_environment_config_returns_current_values(self):
        """Test that get_environment_config returns the current environment values."""
        os.environ["LLMXIVE_SEED"] = "789"
        os.environ["LLMXIVE_MODEL_PATH"] = "another/model"
        os.environ["LLMXIVE_DEVICE"] = "cuda"
        
        config = get_environment_config()
        
        assert config["seed"] == 789
        assert config["model_path"] == "another/model"
        assert config["device"] == "cuda"

    def test_apply_seed_sets_random_seeds(self):
        """Test that apply_seed correctly sets random seeds for reproducibility."""
        seed_value = 999
        apply_seed(seed_value)
        
        # Test that seeds are set by generating some random values
        val1 = random.random()
        np_val1 = np.random.random()
        torch_val1 = torch.rand(1).item()
        
        # Reset and apply seed again
        apply_seed(seed_value)
        
        val2 = random.random()
        np_val2 = np.random.random()
        torch_val2 = torch.rand(1).item()
        
        assert val1 == val2
        assert np_val1 == np_val2
        assert torch_val1 == torch_val2

    def test_apply_seed_uses_environment_variable(self):
        """Test that apply_seed uses the environment variable seed when not provided."""
        os.environ["LLMXIVE_SEED"] = "111"
        apply_seed()  # Should use environment variable
        
        val1 = random.random()
        np_val1 = np.random.random()
        
        # Reset and apply again
        apply_seed()
        
        val2 = random.random()
        np_val2 = np.random.random()
        
        assert val1 == val2
        assert np_val1 == np_val2

    def test_configure_environment_preserves_existing_variables(self):
        """Test that configure_environment doesn't overwrite existing environment variables."""
        os.environ["LLMXIVE_SEED"] = "555"
        os.environ["LLMXIVE_MODEL_PATH"] = "existing/model"
        
        config = configure_environment()
        
        # Should use existing values, not defaults
        assert config["seed"] == 555
        assert config["model_path"] == "existing/model"

    def test_main_function_returns_config(self):
        """Test that main function returns a valid configuration dictionary."""
        # Clear environment first
        for key in list(os.environ.keys()):
            if key.startswith("LLMXIVE_"):
                del os.environ[key]
        
        config = configure_environment()
        
        assert isinstance(config, dict)
        assert "seed" in config
        assert "model_path" in config
        assert "device" in config
        assert "max_turns" in config
        assert "extended_max_turns" in config
        assert "data_raw" in config
        assert "data_processed" in config
        assert "results_path" in config
