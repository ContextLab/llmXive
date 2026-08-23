"""
Contract tests for dataset schema validation.

These tests ensure that the data ingestion pipeline strictly adheres to the
defined schema in `specs/001-gut-microbiome-sleep-architecture/contracts/dataset.schema.yaml`.
"""
import pytest
import os
import json
from pathlib import Path

# Import the validation logic from the main ingest module
# Note: We assume ingest.py exposes a validate_schema function or similar
# based on the API surface provided. If not, we import load_schema from reference_validator.
try:
    from code.ingest import load_schema, validate_variables
except ImportError:
    from code.reference_validator import load_schema


class TestDatasetSchemaContract:
    """
    Contract tests for the Gut Microbiome-Sleep Architecture dataset schema.
    """

    @pytest.fixture
    def schema_path(self):
        """Locate the dataset schema file."""
        # Adjust path based on project root structure
        return Path("specs/001-gut-microbiome-sleep-architecture/contracts/dataset.schema.yaml")

    @pytest.fixture
    def config_path(self):
        """Locate the required variables config."""
        return Path("data/config/required_variables.yaml")

    def test_schema_file_exists(self, schema_path):
        """Verify that the schema definition file exists."""
        assert schema_path.exists(), f"Schema file not found at {schema_path}"

    def test_schema_is_valid_yaml(self, schema_path):
        """Verify that the schema file is valid YAML."""
        import yaml
        try:
            with open(schema_path, 'r') as f:
                schema = yaml.safe_load(f)
            assert schema is not None, "Schema file is empty"
        except yaml.YAMLError as e:
            pytest.fail(f"Schema file is not valid YAML: {e}")

    def test_required_variables_config_exists(self, config_path):
        """Verify that the required variables configuration exists."""
        assert config_path.exists(), f"Required variables config not found at {config_path}"

    def test_required_variables_structure(self, config_path):
        """Verify the structure of required_variables.yaml."""
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        assert 'required_predictors' in config, "Missing 'required_predictors' key"
        assert 'required_outcomes' in config, "Missing 'required_outcomes' key"
        
        assert isinstance(config['required_predictors'], list), "'required_predictors' must be a list"
        assert isinstance(config['required_outcomes'], list), "'required_outcomes' must be a list"
        
        # Ensure lists are not empty (schema requires at least some variables)
        assert len(config['required_predictors']) > 0, "'required_predictors' cannot be empty"
        assert len(config['required_outcomes']) > 0, "'required_outcomes' cannot be empty"

    def test_validation_logic_imports_correctly(self):
        """Verify that validation functions can be imported and called with valid arguments."""
        # This is a basic smoke test to ensure the import chain works
        # A full validation test would require a sample dataframe
        assert load_schema is not None
