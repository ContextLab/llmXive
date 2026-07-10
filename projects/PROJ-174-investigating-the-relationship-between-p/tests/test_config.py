"""
Test configuration validation for T004.

Verifies that code/config.yaml has the correct structure:
- seeds: int (not dict)
- thresholds: dict
- paths: dict
"""

import os
import sys
import yaml
import pytest
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent
sys.path.insert(0, str(code_dir))

from config import load_config


class TestConfigValidation:
    """Tests for configuration file structure and validation."""

    @pytest.fixture
    def config_path(self):
        """Return path to config.yaml."""
        return code_dir / "config.yaml"

    def test_config_file_exists(self, config_path):
        """Test that config.yaml exists."""
        assert config_path.exists(), "config.yaml must exist in code/ directory"

    def test_config_parses_correctly(self, config_path):
        """Test that config.yaml can be parsed without errors."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            assert isinstance(config, dict), "Config must be a dictionary"
        except yaml.YAMLError as e:
            pytest.fail(f"config.yaml failed to parse: {e}")

    def test_seeds_is_integer(self, config_path):
        """Test that 'seeds' key is an integer, not a dictionary."""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        assert 'seeds' in config, "Config must contain 'seeds' key"
        seeds_value = config['seeds']

        # Check that seeds is an integer, not a dict
        assert isinstance(seeds_value, int), (
            f"'seeds' must be an integer, got {type(seeds_value).__name__}. "
            f"Found value: {seeds_value}. Expected format: seeds: 42"
        )

    def test_thresholds_is_dict(self, config_path):
        """Test that 'thresholds' key is a dictionary."""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        assert 'thresholds' in config, "Config must contain 'thresholds' key"
        thresholds_value = config['thresholds']

        assert isinstance(thresholds_value, dict), (
            f"'thresholds' must be a dictionary, got {type(thresholds_value).__name__}"
        )

    def test_paths_is_dict(self, config_path):
        """Test that 'paths' key is a dictionary."""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        assert 'paths' in config, "Config must contain 'paths' key"
        paths_value = config['paths']

        assert isinstance(paths_value, dict), (
            f"'paths' must be a dictionary, got {type(paths_value).__name__}"
        )

    def test_load_config_function(self, config_path):
        """Test that the load_config function works correctly."""
        config = load_config(config_path)

        assert isinstance(config, dict), "load_config must return a dictionary"
        assert 'seeds' in config, "Config must contain 'seeds'"
        assert 'thresholds' in config, "Config must contain 'thresholds'"
        assert 'paths' in config, "Config must contain 'paths'"

        # Verify types
        assert isinstance(config['seeds'], int), "'seeds' must be an integer"
        assert isinstance(config['thresholds'], dict), "'thresholds' must be a dictionary"
        assert isinstance(config['paths'], dict), "'paths' must be a dictionary"

    def test_config_contains_expected_keys(self, config_path):
        """Test that config contains expected keys within each section."""
        config = load_config(config_path)

        # Check seeds (should have at least 'random' if it was a dict, but now it's int)
        # The task spec says seeds: int. The test previously checked for 'random' key.
        # Since seeds is now an int, we verify the int value is present.
        # However, to be robust against the test expecting a 'random' key if the spec
        # implied a dict before, we check the current state: seeds is 42.
        # The test below adapts to the corrected spec: seeds is an int.
        # If the original test expected 'random', we adjust the assertion to match the
        # corrected requirement (seeds: int).
        # The task description says: "seeds (int)".
        # The old test checked 'random' in config['seeds']. Since seeds is now int,
        # we cannot check for keys. We verify the int is non-negative.
        assert config['seeds'] >= 0, "'seeds' must be a non-negative integer"

        # Check thresholds (should have blink, lowpass, vif thresholds)
        required_thresholds = ['blink_threshold', 'lowpass_cutoff', 'vif_threshold']
        for key in required_thresholds:
            assert key in config['thresholds'], f"thresholds must contain '{key}'"

        # Check paths (should have raw_data, processed_data, results)
        required_paths = ['raw_data', 'processed_data', 'results']
        for key in required_paths:
            assert key in config['paths'], f"paths must contain '{key}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])