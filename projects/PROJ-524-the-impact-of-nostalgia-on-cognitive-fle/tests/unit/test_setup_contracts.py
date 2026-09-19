import os
import sys
import pytest
from pathlib import Path
import yaml

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_contracts import create_contracts_directory
from config import get_config


class TestSetupContracts:
    """Unit tests for T007 setup_contracts functionality."""

    def test_create_contracts_directory_exists(self, tmp_path):
        """Test that create_contracts_directory creates the contracts folder."""
        # Create a temporary config
        config = {
            "project_root": str(tmp_path)
        }

        # Call the function
        result = create_contracts_directory(config)

        # Assertions
        assert result is True
        contracts_path = tmp_path / "contracts"
        assert contracts_path.exists()
        assert contracts_path.is_dir()

    def test_create_contracts_directory_creates_placeholders(self, tmp_path):
        """Test that create_contracts_directory creates placeholder schema files."""
        config = {
            "project_root": str(tmp_path)
        }

        result = create_contracts_directory(config)

        assert result is True
        contracts_path = tmp_path / "contracts"

        # Check for placeholder files
        dataset_schema = contracts_path / "dataset.schema.yaml"
        output_schema = contracts_path / "output.schema.yaml"

        assert dataset_schema.exists()
        assert output_schema.exists()

    def test_create_contracts_directory_files_are_valid_yaml(self, tmp_path):
        """Test that the created placeholder files are valid YAML."""
        config = {
            "project_root": str(tmp_path)
        }

        create_contracts_directory(config)

        contracts_path = tmp_path / "contracts"
        dataset_schema = contracts_path / "dataset.schema.yaml"
        output_schema = contracts_path / "output.schema.yaml"

        # Verify YAML parsing
        with open(dataset_schema, 'r') as f:
            dataset_data = yaml.safe_load(f)
            assert isinstance(dataset_data, dict)

        with open(output_schema, 'r') as f:
            output_data = yaml.safe_load(f)
            assert isinstance(output_data, dict)

    def test_create_contracts_directory_idempotent(self, tmp_path):
        """Test that calling create_contracts_directory twice doesn't fail."""
        config = {
            "project_root": str(tmp_path)
        }

        # First call
        result1 = create_contracts_directory(config)
        assert result1 is True

        # Second call should also succeed
        result2 = create_contracts_directory(config)
        assert result2 is True

    def test_contract_directory_structure_matches_requirements(self, tmp_path):
        """Test that the contracts directory contains required files."""
        config = {
            "project_root": str(tmp_path)
        }

        create_contracts_directory(config)

        contracts_path = tmp_path / "contracts"
        required_files = ["dataset.schema.yaml", "output.schema.yaml"]

        for filename in required_files:
            file_path = contracts_path / filename
            assert file_path.exists(), f"Missing required file: {filename}"
            assert file_path.stat().st_size > 0, f"Empty file: {filename}"