"""
Unit tests for the config module (T005).
"""
import pytest
import os
import yaml
import tempfile
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.bias_pipeline.config import (
    load_project_config,
    get_config,
    get_citation_threshold,
    CITATION_TITLE_OVERLAP_THRESHOLD,
    ConfigError,
    _apply_defaults
)


class TestConfigLoading:
    """Tests for loading configuration from YAML."""

    def test_citation_threshold_constant_exists(self):
        """Verify the constant is defined and is a float."""
        assert isinstance(CITATION_TITLE_OVERLAP_THRESHOLD, float)
        assert 0.0 <= CITATION_TITLE_OVERLAP_THRESHOLD <= 1.0

    def test_get_citation_threshold_returns_constant(self):
        """Verify the getter returns the constant value."""
        assert get_citation_threshold() == CITATION_TITLE_OVERLAP_THRESHOLD

    def test_apply_defaults_merges_correctly(self):
        """Test that _apply_defaults properly merges user config with defaults."""
        user_config = {
            "pipeline": {"batch_size": 200},
            "new_key": "value"
        }
        result = _apply_defaults(user_config)
        
        # User override should take precedence
        assert result["pipeline"]["batch_size"] == 200
        
        # Default should remain
        assert result["pipeline"]["max_workers"] == 4
        
        # New key should be present
        assert result["new_key"] == "value"

    def test_apply_defaults_handles_empty_config(self):
        """Test that empty config returns all defaults."""
        result = _apply_defaults({})
        assert result["pipeline"]["batch_size"] == 100
        assert result["bias_detection"]["sentiment_threshold"] == 0.5

    def test_load_project_config_raises_on_missing_file(self):
        """Test that missing config file raises ConfigError."""
        with pytest.raises(ConfigError):
            load_project_config("NON_EXISTENT_PROJECT_ID_12345")

    def test_load_project_config_handles_yaml_error(self):
        """Test that invalid YAML raises ConfigError."""
        # Create a temporary directory and file
        with tempfile.TemporaryDirectory() as tmpdir:
            # Monkey-patch the state directory for this test
            import src.bias_pipeline.config as config_module
            original_state_dir = config_module._STATE_DIR
            
            try:
                config_module._STATE_DIR = Path(tmpdir)
                invalid_yaml_path = Path(tmpdir) / "PROJ-059-automated-detection-of-algorithmic-bias-.yaml"
                invalid_yaml_path.write_text("invalid: yaml: content: [")
                
                with pytest.raises(ConfigError):
                    load_project_config()
            finally:
                config_module._STATE_DIR = original_state_dir

class TestConfigIntegration:
    """Integration tests assuming the project structure exists."""

    def test_get_config_returns_dict(self):
        """Test that get_config returns a dictionary."""
        config = get_config()
        assert isinstance(config, dict)
        assert "pipeline" in config
        assert "bias_detection" in config

    def test_get_config_contains_citation_threshold_in_bias_detection(self):
        """Test that the config contains the citation threshold."""
        config = get_config()
        # Check if the key exists in the loaded config or defaults
        # It might be in bias_detection or at root depending on YAML
        assert "citation_overlap_threshold" in config.get("bias_detection", {})
        assert config["bias_detection"]["citation_overlap_threshold"] == CITATION_TITLE_OVERLAP_THRESHOLD

def test_constants_are_immutable_in_context():
    """Verify that the constant is not accidentally modified during execution."""
    val = CITATION_TITLE_OVERLAP_THRESHOLD
    # Attempt to modify (this will fail in Python for floats, but good for sanity)
    # We just verify it's still the same after a config load
    _ = get_config()
    assert CITATION_TITLE_OVERLAP_THRESHOLD == val
