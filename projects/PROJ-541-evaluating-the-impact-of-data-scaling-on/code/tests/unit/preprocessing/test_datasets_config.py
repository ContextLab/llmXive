import pytest
import yaml
import os
from pathlib import Path
import sys
from preprocessing.ingestion import load_dataset_config

class TestDatasetConfigValidation:
    """
    T034b: Validate the configuration in `data/config/datasets.yaml` created by T027.
    
    This test ensures:
    1. The YAML file exists and is valid.
    2. All dataset IDs are unique.
    3. Required fields (id, name, source) are present.
    4. The file can be loaded by the ingestion module.
    """

    @pytest.fixture
    def config_path(self):
        """Return the path to the datasets.yaml configuration file."""
        return Path("data/config/datasets.yaml")

    def test_file_exists(self, config_path):
        """Assert that the datasets.yaml file exists."""
        assert config_path.exists(), f"Configuration file not found at {config_path}"

    def test_yaml_loads_successfully(self, config_path):
        """Assert that the YAML file can be parsed without errors."""
        with open(config_path, 'r') as f:
            try:
                data = yaml.safe_load(f)
                assert data is not None, "YAML file is empty or invalid"
            except yaml.YAMLError as e:
                pytest.fail(f"Failed to parse YAML: {e}")

    def test_datasets_key_exists(self, config_path):
        """Assert that the 'datasets' key exists in the configuration."""
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
            assert 'datasets' in data, "Missing 'datasets' key in configuration"
            assert isinstance(data['datasets'], list), "'datasets' must be a list"

    def test_unique_dataset_ids(self, config_path):
        """Assert that all dataset IDs are unique."""
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
            ids = [ds['id'] for ds in data['datasets']]
            assert len(ids) == len(set(ids)), "Duplicate dataset IDs found"

    def test_required_fields_present(self, config_path):
        """Assert that all required fields are present in each dataset config."""
        required_fields = ['id', 'name', 'source']
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
            for i, ds in enumerate(data['datasets']):
                for field in required_fields:
                    assert field in ds, f"Missing required field '{field}' in dataset {i}"

    def test_load_dataset_config_function(self, config_path):
        """Assert that the load_dataset_config function works correctly."""
        config = load_dataset_config(config_path)
        assert config is not None, "load_dataset_config returned None"
        assert 'datasets' in config, "Loaded config missing 'datasets' key"
        assert len(config['datasets']) > 0, "Loaded config has no datasets"

    def test_verified_flag_present(self, config_path):
        """Assert that all datasets have a 'verified' flag set to True."""
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
            for ds in data['datasets']:
                assert 'verified' in ds, f"Dataset {ds.get('id', 'unknown')} missing 'verified' flag"
                assert ds['verified'] is True, f"Dataset {ds.get('id', 'unknown')} is not marked as verified"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])