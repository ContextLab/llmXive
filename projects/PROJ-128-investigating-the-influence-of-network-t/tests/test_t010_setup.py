"""
Test suite for Task T010: Setup data directory structure and contracts.
Verifies that directories are created and schema files contain valid YAML.
"""
import os
import sys
import yaml
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the project root to the path to allow imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from setup_data_structure import ensure_directories, create_schema_files

class TestT010Setup:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Create a temporary directory for testing to avoid polluting the real project."""
        # We will test against the actual project structure as per task requirements
        # but ensure we don't break existing files if they exist.
        # Since T010 is about creation, we assume the directories might not exist yet.
        self.base_path = project_root
        yield
        # Cleanup is not strictly necessary for directory creation tests as they are idempotent,
        # but we ensure no temp files are left if we used temp dirs.

    def test_directories_exist(self):
        """Verify that the required data directories are created."""
        # Call the function to ensure directories exist
        ensure_directories()

        expected_dirs = [
            self.base_path / "data" / "raw",
            self.base_path / "data" / "processed",
            self.base_path / "data" / "logs",
            self.base_path / "data" / "figures",
        ]

        for dir_path in expected_dirs:
            assert dir_path.exists(), f"Directory {dir_path} was not created."
            assert dir_path.is_dir(), f"{dir_path} exists but is not a directory."

    def test_contracts_directory_exists(self):
        """Verify that the contracts directory is created."""
        contracts_dir = self.base_path / "contracts"
        assert contracts_dir.exists(), "Contracts directory was not created."
        assert contracts_dir.is_dir(), "Contracts directory exists but is not a directory."

    def test_schema_files_exist(self):
        """Verify that the schema files are created."""
        contracts_dir = self.base_path / "contracts"
        
        dataset_schema = contracts_dir / "dataset.schema.yaml"
        output_schema = contracts_dir / "output.schema.yaml"

        assert dataset_schema.exists(), "dataset.schema.yaml was not created."
        assert output_schema.exists(), "output.schema.yaml was not created."

    def test_schema_files_valid_yaml(self):
        """Verify that the created schema files are valid YAML."""
        contracts_dir = self.base_path / "contracts"
        
        dataset_schema_path = contracts_dir / "dataset.schema.yaml"
        output_schema_path = contracts_dir / "output.schema.yaml"

        try:
            with open(dataset_schema_path, 'r') as f:
                dataset_schema = yaml.safe_load(f)
            assert isinstance(dataset_schema, dict), "dataset.schema.yaml is not a valid YAML object."
            assert "$schema" in dataset_schema, "dataset.schema.yaml missing $schema."
            assert "properties" in dataset_schema, "dataset.schema.yaml missing properties."

            with open(output_schema_path, 'r') as f:
                output_schema = yaml.safe_load(f)
            assert isinstance(output_schema, dict), "output.schema.yaml is not a valid YAML object."
            assert "$schema" in output_schema, "output.schema.yaml missing $schema."
            assert "properties" in output_schema, "output.schema.yaml missing properties."
            
        except yaml.YAMLError as e:
            pytest.fail(f"Schema file is not valid YAML: {e}")

    def test_schema_content_structure(self):
        """Verify that the schema files contain expected keys."""
        contracts_dir = self.base_path / "contracts"
        
        with open(contracts_dir / "dataset.schema.yaml", 'r') as f:
            dataset_schema = yaml.safe_load(f)
        
        assert "subject_id" in dataset_schema["properties"], "Missing subject_id in dataset schema."
        assert "modality" in dataset_schema["properties"], "Missing modality in dataset schema."

        with open(contracts_dir / "output.schema.yaml", 'r') as f:
            output_schema = yaml.safe_load(f)
        
        assert "structural_metrics" in output_schema["properties"], "Missing structural_metrics in output schema."
        assert "dynamic_metrics" in output_schema["properties"], "Missing dynamic_metrics in output schema."
        assert "correlation_results" in output_schema["properties"], "Missing correlation_results in output schema."
        assert "exclusion_log" in output_schema["properties"], "Missing exclusion_log in output schema."