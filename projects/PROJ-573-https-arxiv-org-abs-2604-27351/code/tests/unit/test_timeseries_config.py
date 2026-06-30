"""
Unit tests for timeseries.yaml modality configuration.
Validates FR-008 requirements.
"""
import os
import pytest
import yaml
from pathlib import Path
from datetime import datetime

CONFIG_PATH = Path("src/benchmark/config/modalities/timeseries.yaml")

class TestTimeseriesConfig:
    """Test suite for timeseries modality configuration."""
    
    def test_config_file_exists(self):
        """T040: Verify config file exists at expected path."""
        assert CONFIG_PATH.exists(), f"Config file not found: {CONFIG_PATH}"
    
    def test_config_is_valid_yaml(self):
        """T040: Verify config file is valid YAML."""
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
        assert isinstance(config, dict), "Config must be a dictionary"
    
    def test_required_keys_present(self):
        """T040: Verify all required keys are present (FR-008)."""
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
        
        required_keys = ['model_id', 'model_type', 'max_memory_gb', 'inference_script']
        for key in required_keys:
            assert key in config, f"Missing required key: {key}"
    
    def test_model_id_format(self):
        """T040: Verify model_id is a non-empty string."""
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
        
        assert isinstance(config['model_id'], str)
        assert len(config['model_id']) > 0, "model_id must not be empty"
    
    def test_model_type_valid(self):
        """T040: Verify model_type is TimeSeriesTransformer."""
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
        
        assert config['model_type'] == "TimeSeriesTransformer", \
            f"Expected TimeSeriesTransformer, got {config['model_type']}"
    
    def test_max_memory_gb_constraint(self):
        """T040: Verify max_memory_gb < 1 GB (CPU tractability)."""
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
        
        assert isinstance(config['max_memory_gb'], (int, float))
        assert config['max_memory_gb'] < 1.0, \
            f"max_memory_gb must be < 1 GB for CPU tractability, got {config['max_memory_gb']}"
    
    def test_inference_script_path(self):
        """T040: Verify inference_script points to existing file."""
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
        
        script_path = Path(config['inference_script'])
        assert script_path.exists(), \
            f"Inference script not found: {script_path}"
    
    def test_config_structure(self):
        """T040: Verify config has expected structure for heterogeneous routing."""
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
        
        # Verify metadata fields exist
        assert 'created_by' in config, "Missing created_by field"
        assert 'version' in config, "Missing version field"
        
        # Verify inference parameters
        assert 'inference_params' in config, "Missing inference_params"
        assert 'batch_size' in config['inference_params']
        assert 'timeout_seconds' in config['inference_params']
    
    def test_timestamp_format(self):
        """T040: Verify last_updated is valid ISO format."""
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
        
        last_updated = config.get('last_updated', '')
        try:
            datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
        except ValueError:
            pytest.fail(f"Invalid ISO format timestamp: {last_updated}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])