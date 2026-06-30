import os
import pytest
import yaml
from pathlib import Path
from datetime import datetime

class TestTabularConfig:
    """Test suite for tabular.yaml modality configuration validation."""

    @pytest.fixture
    def config_path(self):
        return Path(__file__).parent.parent.parent / "src" / "benchmark" / "config" / "modalities" / "tabular.yaml"

    @pytest.fixture
    def config(self, config_path):
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def test_config_file_exists(self, config_path):
        """Verify tabular.yaml exists at expected path."""
        assert config_path.exists(), f"Config file not found at {config_path}"

    def test_required_keys_present(self, config):
        """Verify all required keys are present in config."""
        required_keys = ['model_id', 'model_type', 'max_memory_gb', 'inference_script']
        for key in required_keys:
            assert key in config, f"Missing required key: {key}"

    def test_model_type_is_tabular(self, config):
        """Verify model_type is set to 'tabular'."""
        assert config['model_type'] == 'tabular', f"Expected model_type 'tabular', got '{config['model_type']}'"

    def test_max_memory_gb_valid(self, config):
        """Verify max_memory_gb is a positive number <= 1.0 (CPU tractable)."""
        max_mem = config['max_memory_gb']
        assert isinstance(max_mem, (int, float)), "max_memory_gb must be numeric"
        assert 0 < max_mem <= 1.0, f"max_memory_gb must be <= 1.0 for CPU tractability, got {max_mem}"

    def test_inference_script_path_valid(self, config):
        """Verify inference_script points to existing file."""
        script_path = Path(__file__).parent.parent.parent / config['inference_script']
        assert script_path.exists(), f"Inference script not found: {script_path}"

    def test_model_id_defined(self, config):
        """Verify model_id is a non-empty string."""
        assert isinstance(config['model_id'], str), "model_id must be a string"
        assert len(config['model_id']) > 0, "model_id cannot be empty"

    def test_schema_structure(self, config):
        """Verify input and output schema structure."""
        assert 'input_schema' in config, "Missing input_schema"
        assert 'output_schema' in config, "Missing output_schema"
        
        # Check input schema has required fields
        input_schema = config['input_schema']
        assert isinstance(input_schema, list), "input_schema must be a list"
        
        # Check output schema has required fields
        output_schema = config['output_schema']
        assert isinstance(output_schema, list), "output_schema must be a list"

    def test_parameters_structure(self, config):
        """Verify parameters section exists and has expected structure."""
        assert 'parameters' in config, "Missing parameters section"
        assert isinstance(config['parameters'], dict), "parameters must be a dictionary"

    def test_dependencies_list(self, config):
        """Verify dependencies is a list of strings."""
        assert 'dependencies' in config, "Missing dependencies section"
        assert isinstance(config['dependencies'], list), "dependencies must be a list"
        for dep in config['dependencies']:
            assert isinstance(dep, str), "Each dependency must be a string"

    def test_yaml_syntax_valid(self, config_path):
        """Verify YAML syntax is valid."""
        try:
            with open(config_path, 'r') as f:
                yaml.safe_load(f)
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML syntax: {e}")