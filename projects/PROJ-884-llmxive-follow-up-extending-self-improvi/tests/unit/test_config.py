"""
Unit tests for the configuration management module (code/config.py).
"""
import os
import sys
import json
import logging
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure the project root is in the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.config import (
    load_config,
    save_config,
    get_experiment_id,
    initialize_experiment,
    get_default_config,
    DEFAULT_TDP_WATTS,
    main
)
from code.utils.seed import set_seed

class TestDefaultConfig:
    """Tests for default configuration values."""

    def test_default_config_structure(self):
        """Test that the default config contains all required keys."""
        config = get_default_config()
        required_keys = [
            "population_size", "generations", "mutation_rate",
            "crossover_rate", "seed", "tdp_watts", "max_attempts",
            "timeout_seconds", "device"
        ]
        for key in required_keys:
            assert key in config, f"Missing required key: {key}"

    def test_default_tdp_placeholder(self):
        """
        Test that DEFAULT_TDP_WATTS is exactly 0.0 (the placeholder state).
        This is the core requirement for T007b.
        """
        assert DEFAULT_TDP_WATTS == 0.0, \
            f"DEFAULT_TDP_WATTS must be 0.0 (placeholder), but got {DEFAULT_TDP_WATTS}"

    def test_default_config_tdp_is_zero(self):
        """
        Test that the default config's tdp_watts field is 0.0.
        """
        config = get_default_config()
        assert config["tdp_watts"] == 0.0, \
            f"Default config tdp_watts must be 0.0, but got {config['tdp_watts']}"

class TestConfigLoadingAndSaving:
    """Tests for config loading and saving functionality."""

    @pytest.fixture
    def temp_config_file(self, tmp_path):
        """Create a temporary config file for testing."""
        config_path = tmp_path / "test_config.yaml"
        test_config = {
            "population_size": 100,
            "generations": 50,
            "seed": 123,
            "tdp_watts": 65.0  # Non-placeholder value
        }
        with open(config_path, 'w') as f:
            # Simple YAML-like format (no complex YAML features needed)
            for key, value in test_config.items():
                f.write(f"{key}: {value}\n")
        return config_path

    def test_load_config_existing_file(self, temp_config_file):
        """Test loading a configuration from an existing file."""
        config = load_config(str(temp_config_file))
        assert config["population_size"] == 100
        assert config["generations"] == 50
        assert config["tdp_watts"] == 65.0

    def test_load_config_nonexistent_file_logs_warning(self, tmp_path):
        """Test that loading a nonexistent file returns defaults and logs a warning."""
        nonexistent = tmp_path / "does_not_exist.yaml"
        
        with patch('logging.warning') as mock_warning:
            config = load_config(str(nonexistent))
            
            # Verify warning was logged
            assert mock_warning.called
            assert "not found" in str(mock_warning.call_args)
            
            # Verify default config is returned
            assert config["population_size"] == get_default_config()["population_size"]

    def test_save_config_creates_file(self, tmp_path):
        """Test that saving a config creates the file."""
        config_path = tmp_path / "output_config.yaml"
        test_config = {"key": "value", "number": 42}
        
        save_config(test_config, str(config_path))
        
        assert config_path.exists()
        with open(config_path, 'r') as f:
            content = f.read()
            assert "key: value" in content
            assert "number: 42" in content

class TestExperimentInitialization:
    """Tests for experiment initialization logic."""

    def test_initialize_experiment_with_config(self):
        """Test initializing an experiment with a provided config."""
        test_config = {
            "population_size": 50,
            "seed": 42,
            "tdp_watts": 65.0  # Calibrated value
        }
        
        # Mock logging to avoid cluttering test output
        with patch('logging.warning') as mock_warning:
            result = initialize_experiment(test_config)
            
            # Verify the config is returned
            assert result["population_size"] == 50
            assert result["seed"] == 42
            
            # Verify NO warning about TDP (since it's calibrated)
            tdp_warnings = [call for call in mock_warning.call_args_list 
                            if "TDP calibration" in str(call)]
            assert len(tdp_warnings) == 0

    def test_initialize_experiment_with_placeholder_tdp_logs_warning(self):
        """
        Test that initializing with a placeholder TDP (0.0) logs a warning.
        This verifies the T007b requirement for warning on missing calibration.
        """
        test_config = {
            "population_size": 50,
            "seed": 42,
            "tdp_watts": 0.0  # Placeholder value
        }
        
        with patch('logging.warning') as mock_warning:
            initialize_experiment(test_config)
            
            # Verify warning was logged about TDP
            tdp_warnings = [call for call in mock_warning.call_args_list 
                            if "TDP calibration not detected" in str(call)]
            assert len(tdp_warnings) == 1, \
                "Expected a warning about TDP calibration when tdp_watts is 0.0"

    def test_initialize_experiment_missing_tdp_field_logs_warning(self):
        """
        Test that initializing with a config missing the tdp_watts field
        logs a warning (defaults to 0.0).
        """
        test_config = {
            "population_size": 50,
            "seed": 42
            # tdp_watts is missing
        }
        
        with patch('logging.warning') as mock_warning:
            initialize_experiment(test_config)
            
            # Verify warning was logged
            tdp_warnings = [call for call in mock_warning.call_args_list 
                            if "TDP calibration not detected" in str(call)]
            assert len(tdp_warnings) == 1

class TestExperimentIdGeneration:
    """Tests for experiment ID generation."""

    def test_experiment_id_format(self):
        """Test that experiment IDs follow the expected format."""
        set_seed(42)
        exp_id = get_experiment_id()
        
        # Format should be: exp_{seed}_{timestamp}
        assert exp_id.startswith("exp_")
        parts = exp_id.split("_")
        assert len(parts) >= 3  # exp, seed, timestamp (which may have underscores)
        assert parts[1] == "42"  # The seed we set

class TestMainFunction:
    """Tests for the main entry point."""

    def test_main_executes_without_error(self, capsys):
        """Test that the main function runs without exceptions."""
        # This is a basic smoke test
        try:
            main()
        except Exception as e:
            pytest.fail(f"main() raised an exception: {e}")

# T007b specific verification test
def test_tdp_placeholder_exists():
    """
    T007b Verification: Asserts the key exists AND that its value is exactly 0.0.
    This is the explicit verification requirement from the task description.
    """
    # 1. Assert the key exists in DEFAULT_TDP_WATTS constant
    assert hasattr(sys.modules['code.config'], 'DEFAULT_TDP_WATTS'), \
        "DEFAULT_TDP_WATTS constant must exist in code.config"
    
    # 2. Assert its value is exactly 0.0
    assert DEFAULT_TDP_WATTS == 0.0, \
        f"DEFAULT_TDP_WATTS must be exactly 0.0 (placeholder), but got {DEFAULT_TDP_WATTS}"
    
    # 3. Assert it appears in the default config
    config = get_default_config()
    assert "tdp_watts" in config, "tdp_watts must exist in default config"
    assert config["tdp_watts"] == 0.0, \
        f"Default config tdp_watts must be 0.0, but got {config['tdp_watts']}"