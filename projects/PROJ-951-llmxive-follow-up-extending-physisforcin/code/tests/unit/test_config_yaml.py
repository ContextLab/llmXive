"""
Unit tests for T007b: Config YAML validation and schema enforcement.
"""
import os
import tempfile
import pytest
import yaml
from pathlib import Path
from src.training.config import (
    load_config,
    validate_config_schema,
    get_filter_discard_threshold,
    ProjectConfig,
    FilteringConfig
)

class TestConfigYAML:
    """Tests for the config.yaml file and its schema validation."""

    def test_config_file_exists(self):
        """Verify that config.yaml exists at the expected path."""
        config_path = Path("code/config.yaml")
        assert config_path.exists(), "config.yaml must exist"

    def test_filter_discard_percent_is_0_4(self):
        """Verify that filter_discard_percent is explicitly set to 0.4."""
        config_path = Path("code/config.yaml")
        with open(config_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        
        assert config_dict['filtering']['filter_discard_percent'] == 0.4, \
            "filter_discard_percent must be 0.4 to resolve FR-003"

    def test_schema_validation_required_keys(self):
        """Test that schema validation catches missing required keys."""
        valid_dict = {
            "project_id": "test",
            "environment": {"cpu_only": True},
            "data": {"root": "data"},
            "filtering": {"filter_discard_percent": 0.4},
            "training": {"seed": 42}
        }
        
        is_valid, errors = validate_config_schema(valid_dict)
        assert is_valid, f"Valid config should pass validation: {errors}"

        # Test missing key
        invalid_dict = valid_dict.copy()
        del invalid_dict['project_id']
        
        is_valid, errors = validate_config_schema(invalid_dict)
        assert not is_valid
        assert any("project_id" in err for err in errors)

    def test_schema_validation_type_checks(self):
        """Test that schema validation catches type mismatches."""
        valid_dict = {
            "project_id": "test",
            "environment": {"cpu_only": True},
            "data": {"root": "data"},
            "filtering": {"filter_discard_percent": 0.4},
            "training": {"seed": 42, "epochs": 10},
            "environment": {"max_ram_gb": 6.0}
        }
        
        is_valid, errors = validate_config_schema(valid_dict)
        assert is_valid

        # Test wrong type
        invalid_dict = valid_dict.copy()
        invalid_dict['filtering']['filter_discard_percent'] = "0.4"  # String instead of float
        
        is_valid, errors = validate_config_schema(invalid_dict)
        assert not is_valid
        assert any("filter_discard_percent" in err for err in errors)

    def test_schema_validation_value_ranges(self):
        """Test that schema validation catches out-of-range values."""
        valid_dict = {
            "project_id": "test",
            "environment": {"cpu_only": True},
            "data": {"root": "data"},
            "filtering": {"filter_discard_percent": 0.4},
            "training": {"seed": 42, "batch_size": 4},
            "environment": {"max_ram_gb": 6.0}
        }
        
        is_valid, errors = validate_config_schema(valid_dict)
        assert is_valid

        # Test out of range
        invalid_dict = valid_dict.copy()
        invalid_dict['filtering']['filter_discard_percent'] = 1.5  # > 1.0
        
        is_valid, errors = validate_config_schema(invalid_dict)
        assert not is_valid
        assert any("filter_discard_percent" in err for err in errors)

    def test_load_config_from_yaml(self):
        """Test loading the actual config.yaml file."""
        config = load_config("code/config.yaml")
        
        assert config.project_id == "PROJ-951-llmxive-follow-up-extending-physisforcin"
        assert config.filtering.filter_discard_percent == 0.4
        assert config.environment.cpu_only is True

    def test_get_filter_discard_threshold(self):
        """Test the get_filter_discard_threshold helper function."""
        config = load_config("code/config.yaml")
        threshold = get_filter_discard_threshold(config)
        
        assert threshold == 0.4

    def test_config_schema_completeness(self):
        """Verify that all keys defined in config.yaml are loadable."""
        config_path = Path("code/config.yaml")
        with open(config_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        
        config = load_config("code/config.yaml")
        
        # Verify top-level keys
        assert hasattr(config, 'project_id')
        assert hasattr(config, 'environment')
        assert hasattr(config, 'data')
        assert hasattr(config, 'generation')
        assert hasattr(config, 'filtering')
        assert hasattr(config, 'training')
        assert hasattr(config, 'evaluation')
        assert hasattr(config, 'logging')

    def test_filtering_section_structure(self):
        """Verify the filtering section has all required keys."""
        config = load_config("code/config.yaml")
        
        assert hasattr(config.filtering, 'filter_discard_percent')
        assert hasattr(config.filtering, 'physics_engine')
        assert hasattr(config.filtering, 'simulation_steps')
        assert hasattr(config.filtering, 'continuity_threshold')
        assert hasattr(config.filtering, 'contact_threshold')
        assert hasattr(config.filtering, 'headless_mode')