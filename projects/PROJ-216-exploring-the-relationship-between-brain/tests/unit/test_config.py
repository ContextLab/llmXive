"""
Unit tests for the configuration module (T010).
Verifies YAML syntax, key presence, and value retrieval.
"""
import pytest
import os
import tempfile
import yaml
from pathlib import Path
import sys

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import get_dataset_ids, get_sample_limit, get_config_summary, validate_config, CONFIG_PATH

class TestConfigKeys:
    """Tests for the existence and correctness of config keys."""

    def test_config_file_exists(self):
        """Verify that config.yaml exists in the project root."""
        assert CONFIG_PATH.exists(), f"config.yaml not found at {CONFIG_PATH}"

    def test_yaml_syntax_valid(self):
        """Verify that config.yaml has valid YAML syntax."""
        try:
            with open(CONFIG_PATH, "r") as f:
                yaml.safe_load(f)
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML syntax in config.yaml: {e}")

    def test_primary_dataset_key_present(self):
        """Verify 'datasets.primary' key is present."""
        config = yaml.safe_load(open(CONFIG_PATH, "r"))
        assert "datasets" in config
        assert "primary" in config["datasets"]

    def test_fallback_dataset_key_present(self):
        """Verify 'datasets.fallback_only' key is present."""
        config = yaml.safe_load(open(CONFIG_PATH, "r"))
        assert "datasets" in config
        assert "fallback_only" in config["datasets"]

    def test_sample_limit_key_present(self):
        """Verify 'sample_limit' key is present."""
        config = yaml.safe_load(open(CONFIG_PATH, "r"))
        assert "sample_limit" in config

class TestConfigValues:
    """Tests for the correctness of config values."""

    def test_primary_dataset_is_ds000224(self):
        """Verify primary dataset ID is ds000224."""
        primary, _ = get_dataset_ids()
        assert primary == "ds000224", f"Expected primary 'ds000224', got '{primary}'"

    def test_fallback_dataset_is_ds000230(self):
        """Verify fallback dataset ID is ds000230."""
        _, fallback = get_dataset_ids()
        assert fallback == "ds000230", f"Expected fallback 'ds000230', got '{fallback}'"

    def test_sample_limit_is_10(self):
        """Verify sample limit is 10."""
        limit = get_sample_limit()
        assert limit == 10, f"Expected sample_limit 10, got {limit}"

    def test_get_config_summary_structure(self):
        """Verify get_config_summary returns correct structure."""
        summary = get_config_summary()
        assert "primary_dataset" in summary
        assert "fallback_dataset" in summary
        assert "sample_limit" in summary
        assert summary["primary_dataset"] == "ds000224"
        assert summary["fallback_dataset"] == "ds000230"
        assert summary["sample_limit"] == 10

class TestConfigValidation:
    """Tests for config validation logic."""

    def test_validate_config_returns_true(self):
        """Verify validate_config returns True for valid config."""
        assert validate_config() is True

    def test_validate_config_raises_on_missing_key(self):
        """Verify validation fails if a required key is missing."""
        # Create a temporary invalid config
        invalid_config = {
            "datasets": {"primary": "ds000224"}, # Missing fallback
            "sample_limit": 10
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(invalid_config, f)
            temp_path = f.name

        try:
            # Temporarily override CONFIG_PATH
            import config as cfg_module
            original_path = cfg_module.CONFIG_PATH
            cfg_module.CONFIG_PATH = Path(temp_path)
            
            with pytest.raises(ValueError, match="missing"):
                validate_config()
        finally:
            # Restore original path and clean up
            cfg_module.CONFIG_PATH = original_path
            os.unlink(temp_path)

    def test_validate_config_raises_on_invalid_limit(self):
        """Verify validation fails if sample_limit is invalid."""
        invalid_config = {
            "datasets": {"primary": "ds000224", "fallback_only": "ds000230"},
            "sample_limit": -5
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(invalid_config, f)
            temp_path = f.name

        try:
            import config as cfg_module
            original_path = cfg_module.CONFIG_PATH
            cfg_module.CONFIG_PATH = Path(temp_path)
            
            with pytest.raises(ValueError, match="positive"):
                validate_config()
        finally:
            cfg_module.CONFIG_PATH = original_path
            os.unlink(temp_path)
