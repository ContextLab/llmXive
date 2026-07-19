import pytest
import yaml
import os
from pathlib import Path
import sys

# Ensure the code directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from preprocessing.ingestion import load_dataset_config

class TestDatasetConfigValidation:
    """
    Tests for T027: Create Verified Dataset Configuration.
    Validates that data/config/datasets.yaml exists, is unique, and accessible.
    """

    @pytest.fixture
    def config_path(self):
        return Path("data/config/datasets.yaml")

    def test_config_file_exists(self, config_path):
        """Verify that the datasets.yaml configuration file exists."""
        assert config_path.exists(), f"Configuration file {config_path} does not exist."

    def test_config_loads_valid_yaml(self, config_path):
        """Verify that the configuration file is valid YAML."""
        try:
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f)
            assert isinstance(data, dict), "Root element must be a dictionary."
            assert 'datasets' in data, "Root dictionary must contain 'datasets' key."
            assert isinstance(data['datasets'], list), "'datasets' must be a list."
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in {config_path}: {e}")

    def test_unique_dataset_ids(self, config_path):
        """Verify that all dataset IDs in the configuration are unique."""
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        
        ids = [ds['id'] for ds in data['datasets']]
        seen = set()
        duplicates = []
        for ds_id in ids:
            if ds_id in seen:
                duplicates.append(ds_id)
            seen.add(ds_id)
        
        assert len(duplicates) == 0, f"Duplicate dataset IDs found: {duplicates}"

    def test_required_fields_present(self, config_path):
        """Verify that each dataset entry has required fields: id, source, description."""
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        
        required_fields = ['id', 'source', 'description']
        for i, ds in enumerate(data['datasets']):
            for field in required_fields:
                assert field in ds, f"Dataset at index {i} is missing required field: {field}"

    def test_load_dataset_config_function_exists(self):
        """Verify that the load_dataset_config function exists and is callable."""
        assert callable(load_dataset_config), "load_dataset_config must be callable."

    def test_load_dataset_config_returns_list(self, config_path):
        """Verify that load_dataset_config returns a list of datasets."""
        datasets = load_dataset_config(config_path)
        assert isinstance(datasets, list), "load_dataset_config must return a list."
        assert len(datasets) > 0, "load_dataset_config must return a non-empty list."

    def test_load_dataset_config_preserves_fields(self, config_path):
        """Verify that load_dataset_config preserves all fields from YAML."""
        datasets = load_dataset_config(config_path)
        for ds in datasets:
            assert 'id' in ds
            assert 'source' in ds
            assert 'description' in ds
            # Optional fields check
            assert 'type' in ds or 'expected_size' in ds, "Each dataset should have at least 'type' or 'expected_size'."

    def test_config_ids_are_formatted_correctly(self, config_path):
        """Verify that dataset IDs follow the expected format (e.g., 'uciml/iris' or 'openml/d/2')."""
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        
        valid_prefixes = ['uciml/', 'openml/d/']
        for ds in data['datasets']:
            ds_id = ds['id']
            assert any(ds_id.startswith(prefix) for prefix in valid_prefixes), \
                f"Dataset ID '{ds_id}' does not start with a valid prefix (uciml/ or openml/d/)."
            
            # Additional check: no spaces in IDs
            assert ' ' not in ds_id, f"Dataset ID '{ds_id}' contains spaces."
            
            # Additional check: no trailing slashes
            assert not ds_id.endswith('/'), f"Dataset ID '{ds_id}' ends with a slash."

    def test_no_empty_descriptions(self, config_path):
        """Verify that no dataset has an empty or whitespace-only description."""
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        
        for i, ds in enumerate(data['datasets']):
            desc = ds.get('description', '')
            assert desc.strip(), f"Dataset at index {i} has an empty or whitespace-only description."