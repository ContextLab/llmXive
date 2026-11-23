import os
import pytest
from pathlib import Path
import yaml


class TestContractsStructure:
    """
    Contract test to verify the contracts/ directory structure exists
    and contains expected schema files.
    """

    @pytest.fixture
    def contracts_dir(self):
        """Get the contracts directory path."""
        return Path("contracts")

    def test_contracts_directory_exists(self, contracts_dir):
        """Verify the contracts/ directory exists."""
        assert contracts_dir.exists(), "contracts/ directory must exist"
        assert contracts_dir.is_dir(), "contracts/ must be a directory"

    def test_dataset_schema_exists(self, contracts_dir):
        """Verify dataset.schema.yaml exists in contracts/."""
        schema_file = contracts_dir / "dataset.schema.yaml"
        assert schema_file.exists(), "contracts/dataset.schema.yaml must exist"

    def test_output_schema_exists(self, contracts_dir):
        """Verify output.schema.yaml exists in contracts/."""
        schema_file = contracts_dir / "output.schema.yaml"
        assert schema_file.exists(), "contracts/output.schema.yaml must exist"

    def test_dataset_schema_is_valid_yaml(self, contracts_dir):
        """Verify dataset.schema.yaml contains valid YAML."""
        schema_file = contracts_dir / "dataset.schema.yaml"
        try:
            with open(schema_file, "r") as f:
                data = yaml.safe_load(f)
            assert data is not None, "dataset.schema.yaml must not be empty"
            assert isinstance(data, dict), "dataset.schema.yaml must be a YAML mapping"
        except yaml.YAMLError as e:
            pytest.fail(f"dataset.schema.yaml is not valid YAML: {e}")

    def test_output_schema_is_valid_yaml(self, contracts_dir):
        """Verify output.schema.yaml contains valid YAML."""
        schema_file = contracts_dir / "output.schema.yaml"
        try:
            with open(schema_file, "r") as f:
                data = yaml.safe_load(f)
            assert data is not None, "output.schema.yaml must not be empty"
            assert isinstance(data, dict), "output.schema.yaml must be a YAML mapping"
        except yaml.YAMLError as e:
            pytest.fail(f"output.schema.yaml is not valid YAML: {e}")

    def test_dataset_schema_has_required_fields(self, contracts_dir):
        """Verify dataset.schema.yaml defines required fields."""
        schema_file = contracts_dir / "dataset.schema.yaml"
        with open(schema_file, "r") as f:
            data = yaml.safe_load(f)
        
        required_fields = ["participant_id", "age", "stimulus_type", 
                         "perseverative_errors", "categories_completed"]
        
        properties = data.get("properties", {})
        for field in required_fields:
            assert field in properties, f"dataset.schema.yaml must define '{field}'"

    def test_output_schema_has_required_fields(self, contracts_dir):
        """Verify output.schema.yaml defines required output fields."""
        schema_file = contracts_dir / "output.schema.yaml"
        with open(schema_file, "r") as f:
            data = yaml.safe_load(f)
        
        # Output schema should have at least some structure
        assert "type" in data or "properties" in data, \
            "output.schema.yaml must define a valid schema structure"
