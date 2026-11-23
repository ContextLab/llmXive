"""
Tests for the environment configuration management module.

These tests verify that CPU-only flags are correctly set and
environment variables are configured as expected.
"""

import pytest
import os
import json
from pathlib import Path
import tempfile

# Import the module under test
from setup_environment_config import EnvironmentConfig, get_env_config


class TestEnvironmentConfig:
    """Test suite for the EnvironmentConfig class."""

    def test_default_cpu_only_initialization(self):
        """Test that CPU-only mode is enabled by default."""
        config = EnvironmentConfig()
        assert config.cpu_only is True
        assert config.device == "cpu"
        assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""

    def test_explicit_cpu_only_false(self):
        """Test initialization with CPU-only disabled."""
        config = EnvironmentConfig(cpu_only=False)
        assert config.cpu_only is False
        assert config.device == "cuda"
        # Note: CUDA_VISIBLE_DEVICES might not be reset to empty if it was set before,
        # but the logic in __init__ only sets it if cpu_only is True.
        # We verify the logic holds for the True case primarily.

    def test_num_threads_configuration(self):
        """Test that thread count is set correctly."""
        config = EnvironmentConfig(num_threads=8)
        assert config.num_threads == 8
        assert os.environ.get("OMP_NUM_THREADS") == "8"
        assert os.environ.get("MKL_NUM_THREADS") == "8"

    def test_config_save_and_load(self, tmp_path):
        """Test saving and loading configuration to/from a file."""
        config_path = tmp_path / "test_env_config.json"
        
        # Create and save
        original_config = EnvironmentConfig(cpu_only=True, num_threads=2, verbose=True)
        original_config.save(config_path)
        
        assert config_path.exists()
        
        # Load
        loaded_config = EnvironmentConfig.load(config_path)
        
        assert loaded_config.cpu_only == original_config.cpu_only
        assert loaded_config.num_threads == original_config.num_threads
        assert loaded_config.verbose == original_config.verbose
        assert loaded_config.device == original_config.device

    def test_to_dict_serialization(self):
        """Test that configuration converts to dictionary correctly."""
        config = EnvironmentConfig(cpu_only=False, num_threads=1, verbose=False)
        data = config.to_dict()
        
        assert isinstance(data, dict)
        assert data["cpu_only"] is False
        assert data["device"] == "cuda"
        assert data["num_threads"] == 1
        assert data["verbose"] is False

    def test_validate_valid_config(self):
        """Test validation of a valid configuration."""
        config = EnvironmentConfig(cpu_only=True, num_threads=4)
        assert config.validate() is True

    def test_validate_invalid_threads(self):
        """Test validation fails with invalid thread count."""
        config = EnvironmentConfig(cpu_only=True, num_threads=0)
        assert config.validate() is False

    def test_validate_cpu_gpu_conflict(self):
        """Test validation catches device mismatch."""
        # Create a config where cpu_only is False but we manually force device to cpu
        # (Simulating a potential state error)
        config = EnvironmentConfig(cpu_only=False)
        config.device = "cpu" # Manually override to simulate error state
        # The validate method checks: if not self.cpu_only and self.device != "cuda"
        assert config.validate() is False


class TestGetEnvConfig:
    """Test suite for the get_env_config factory function."""

    def test_env_variable_override_cpu_only(self, monkeypatch):
        """Test that environment variables override defaults."""
        monkeypatch.setenv("LLMXIVE_CPU_ONLY", "false")
        monkeypatch.setenv("LLMXIVE_NUM_THREADS", "8")
        
        config = get_env_config()
        
        assert config.cpu_only is False
        assert config.num_threads == 8

    def test_env_variable_invalid_threads(self, monkeypatch, caplog):
        """Test handling of invalid thread count in environment variable."""
        monkeypatch.setenv("LLMXIVE_NUM_THREADS", "not_a_number")
        
        config = get_env_config()
        
        assert config.num_threads == 4 # Should default to 4
        assert "Invalid LLMXIVE_NUM_THREADS" in caplog.text

    def test_default_values_without_env(self, monkeypatch):
        """Test defaults when no environment variables are set."""
        # Ensure env vars are not set
        for key in ["LLMXIVE_CPU_ONLY", "LLMXIVE_NUM_THREADS", "LLMXIVE_VERBOSE"]:
            monkeypatch.delenv(key, raising=False)
        
        config = get_env_config()
        
        assert config.cpu_only is True
        assert config.num_threads == 4
        assert config.verbose is False
