"""
Tests for contract schema files.
Verifies that all required schema files exist and are valid YAML.
"""
import os
import sys
import yaml
import json
from pathlib import Path
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

REQUIRED_SCHEMAS = {
    "dataset.schema.yaml": ["schema_version", "artifact_type", "required_arrays", "required_metadata", "validation_rules"],
    "model_output.schema.yaml": ["schema_version", "artifact_type", "architecture", "checkpoint_contents", "validation_rules"],
    "evaluation_results.schema.yaml": ["schema_version", "artifact_type", "required_sections", "validation_rules"]
}

class TestContractSchemas:
    """Test suite for contract schema files."""

    def test_schema_files_exist(self):
        """Verify that all required schema files exist."""
        for schema_name in REQUIRED_SCHEMAS.keys():
            schema_path = CONTRACTS_DIR / schema_name
            assert schema_path.exists(), f"Schema file missing: {schema_name}"

    def test_yaml_syntax(self):
        """Verify that all schema files are valid YAML."""
        for schema_name in REQUIRED_SCHEMAS.keys():
            schema_path = CONTRACTS_DIR / schema_name
            with open(schema_path, 'r') as f:
                try:
                    yaml.safe_load(f)
                except yaml.YAMLError as e:
                    pytest.fail(f"Invalid YAML in {schema_name}: {e}")

    def test_required_keys(self):
        """Verify that each schema file contains required top-level keys."""
        for schema_name, required_keys in REQUIRED_SCHEMAS.items():
            schema_path = CONTRACTS_DIR / schema_name
            with open(schema_path, 'r') as f:
                data = yaml.safe_load(f)
            
            for key in required_keys:
                assert key in data, f"Missing required key '{key}' in {schema_name}"

    def test_schema_version(self):
        """Verify that all schemas have a valid version."""
        for schema_name in REQUIRED_SCHEMAS.keys():
            schema_path = CONTRACTS_DIR / schema_name
            with open(schema_path, 'r') as f:
                data = yaml.safe_load(f)
            
            assert 'schema_version' in data
            assert isinstance(data['schema_version'], str)
            # Basic version format check (e.g., "1.0")
            assert any(c.isdigit() for c in data['schema_version']), \
                f"Invalid version format in {schema_name}"

    def test_artifact_type(self):
        """Verify that all schemas specify an artifact type."""
        valid_types = ["dataset", "model_checkpoint", "evaluation_report"]
        
        for schema_name in REQUIRED_SCHEMAS.keys():
            schema_path = CONTRACTS_DIR / schema_name
            with open(schema_path, 'r') as f:
                data = yaml.safe_load(f)
            
            assert 'artifact_type' in data
            assert data['artifact_type'] in valid_types, \
                f"Invalid artifact_type '{data['artifact_type']}' in {schema_name}"

    def test_validation_rules_exist(self):
        """Verify that all schemas have validation rules defined."""
        for schema_name in REQUIRED_SCHEMAS.keys():
            schema_path = CONTRACTS_DIR / schema_name
            with open(schema_path, 'r') as f:
                data = yaml.safe_load(f)
            
            assert 'validation_rules' in data
            assert isinstance(data['validation_rules'], list), \
                f"validation_rules must be a list in {schema_name}"
            assert len(data['validation_rules']) > 0, \
                f"validation_rules is empty in {schema_name}"

    def test_dataset_schema_structure(self):
        """Specific tests for dataset.schema.yaml structure."""
        schema_path = CONTRACTS_DIR / "dataset.schema.yaml"
        with open(schema_path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Check required arrays
        assert 'required_arrays' in data
        required_arrays = data['required_arrays']
        assert len(required_arrays) > 0
        
        array_names = [arr['name'] for arr in required_arrays]
        expected_arrays = ['ir_spectra', 'wavenumbers', 'dipole_moment', 
                         'polarizability', 'homo_lumo_gap', 'inchi_keys', 'molecule_ids']
        
        for expected in expected_arrays:
            assert expected in array_names, f"Missing array '{expected}' in dataset schema"

    def test_model_output_schema_structure(self):
        """Specific tests for model_output.schema.yaml structure."""
        schema_path = CONTRACTS_DIR / "model_output.schema.yaml"
        with open(schema_path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Check architecture definition
        assert 'architecture' in data
        assert 'heads' in data['architecture']
        
        head_names = [h['name'] for h in data['architecture']['heads']]
        expected_heads = ['dipole_moment', 'polarizability', 'homo_lumo_gap']
        
        for expected in expected_heads:
            assert expected in head_names, f"Missing head '{expected}' in model schema"

    def test_evaluation_results_schema_structure(self):
        """Specific tests for evaluation_results.schema.yaml structure."""
        schema_path = CONTRACTS_DIR / "evaluation_results.schema.yaml"
        with open(schema_path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Check required sections
        assert 'required_sections' in data
        sections = data['required_sections']
        
        assert 'primary_metrics' in sections
        assert 'statistical_tests' in sections
        assert 'summary' in sections