"""
Unit tests for the CA Engine configuration loader and schema validation.
"""
import pytest
import os
import tempfile
from pathlib import Path
import yaml

# Import the module under test
# Assuming the package structure allows direct import or we adjust sys.path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from sim.config_loader import load_config, validate_schema

class TestSchemaValidation:
    """Tests for T004a: Schema loading and validation."""

    def test_validate_schema_loads_without_error(self):
        """
        T004a Requirement: Validate schema loads without error.
        Tests that the default config_schema.yaml is valid YAML and structurally correct.
        """
        # This should not raise an exception
        result = validate_schema()
        assert result is True

    def test_schema_contains_required_sections(self):
        """
        Verifies the schema file contains the required sections:
        locality, memory, non-linearity.
        """
        # Re-load the raw file to check keys directly
        schema_path = Path(__file__).parent.parent.parent / 'src' / 'sim' / 'config_schema.yaml'
        with open(schema_path, 'r') as f:
            data = yaml.safe_load(f)
        
        config = data['config']
        assert 'locality' in config
        assert 'memory' in config
        assert 'non_linearity' in config
        assert 'engine' in config
        assert 'simulation' in config

class TestConfigLoading:
    """Tests for the load_config function."""

    def test_load_default_config(self):
        """Tests loading the default configuration from the schema file."""
        config = load_config()
        
        assert 'engine' in config
        assert config['engine']['type'] == 'ca'
        assert 'locality' in config
        assert 'memory' in config
        assert 'non_linearity' in config
        assert 'simulation' in config
        assert 'steps' in config['simulation']

    def test_load_custom_config(self):
        """Tests loading a custom configuration file."""
        custom_config = {
            'engine': {'type': 'ca', 'grid_type': '2d', 'boundary_condition': 'periodic'},
            'locality': {'radius': 2, 'kernel_type': 'moore', 'weight_decay': 0.1},
            'memory': {'history_depth': 5, 'persistence_threshold': 0.6, 'decay_factor': 0.8},
            'non_linearity': {'activation': 'tanh', 'sensitivity': 2.0, 'noise_scale': 0.05},
            'simulation': {'steps': 5000, 'seed': 123, 'verbose': True}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(custom_config, f)
            temp_path = f.name

        try:
            loaded_config = load_config(temp_path)
            assert loaded_config['simulation']['steps'] == 5000
            assert loaded_config['locality']['radius'] == 2
        finally:
            os.unlink(temp_path)

    def test_load_missing_file_raises_error(self):
        """Tests that loading a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_config("/path/to/nonexistent/file.yaml")

    def test_invalid_yaml_raises_error(self):
        """Tests that an invalid YAML file raises an error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name

        try:
            with pytest.raises(RuntimeError): # load_config wraps yaml errors in RuntimeError for schema, but direct load might raise YAMLError
                # Actually, load_config calls yaml.safe_load which raises YAMLError.
                # Let's test the direct behavior or ensure our wrapper handles it.
                # The current load_config catches yaml.YAMLError and raises RuntimeError.
                load_config(temp_path)
        finally:
            os.unlink(temp_path)
