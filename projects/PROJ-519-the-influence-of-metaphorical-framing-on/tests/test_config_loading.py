"""
Test suite for configuration loading and validation.
Ensures that simulation_config.yaml is parsed correctly and
environment variables are loaded as expected.
"""
import os
import yaml
import pytest
from pathlib import Path

# Import the config loader (placeholder for future implementation if needed,
# currently testing direct file access or simple parsing)
# For now, we test the existence and basic structure of the config file.

CONFIG_PATH = Path(__file__).parent.parent / "config" / "simulation_config.yaml"
ENV_EXAMPLE_PATH = Path(__file__).parent.parent / "config" / ".env.example"

class TestConfigStructure:
    """Tests to verify the config file exists and has required keys."""

    def test_config_file_exists(self):
        """Verify simulation_config.yaml exists."""
        assert CONFIG_PATH.exists(), f"Config file not found at {CONFIG_PATH}"

    def test_config_is_valid_yaml(self):
        """Verify the config file is valid YAML."""
        with open(CONFIG_PATH, "r") as f:
            try:
                config = yaml.safe_load(f)
                assert isinstance(config, dict), "Config must be a dictionary"
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in config: {e}")

    def test_required_keys_present(self):
        """Verify critical configuration keys are present."""
        with open(CONFIG_PATH, "r") as f:
            config = yaml.safe_load(f)

        required_keys = [
            "random_seed",
            "synthetic_data",
            "execution_limits",
            "features"
        ]

        for key in required_keys:
            assert key in config, f"Missing required key: {key}"

    def test_synthetic_data_structure(self):
        """Verify synthetic_data section has correct sub-keys."""
        with open(CONFIG_PATH, "r") as f:
            config = yaml.safe_load(f)

        sd = config.get("synthetic_data", {})
        assert "corpus_size" in sd, "Missing corpus_size in synthetic_data"
        assert "condition_distribution" in sd, "Missing condition_distribution"
        assert "corpus_size" in sd and sd["corpus_size"] > 0

    def test_execution_limits_structure(self):
        """Verify execution_limits section has correct sub-keys."""
        with open(CONFIG_PATH, "r") as f:
            config = yaml.safe_load(f)

        el = config.get("execution_limits", {})
        assert "MAX_RUNTIME_SECONDS" in el, "Missing MAX_RUNTIME_SECONDS"
        assert "SAMPLE_SIZE_FALLBACK" in el, "Missing SAMPLE_SIZE_FALLBACK"

    def test_env_example_exists(self):
        """Verify .env.example exists."""
        assert ENV_EXAMPLE_PATH.exists(), f".env.example not found at {ENV_EXAMPLE_PATH}"

    def test_env_example_has_content(self):
        """Verify .env.example is not empty."""
        with open(ENV_EXAMPLE_PATH, "r") as f:
            content = f.read()
        assert len(content) > 0, ".env.example is empty"
        assert "PUSHSHIFT_API_KEY" in content or "DATA_DIR" in content, \
            ".env.example should contain example variables"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
