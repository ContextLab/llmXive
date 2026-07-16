"""
Contract tests for data schema validation.
Validates that generated data files match the schema definitions in contracts/data_schema.yaml.
"""

import pytest
import pandas as pd
import json
import yaml
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.schema_validator import load_schema, validate_csv_schema, validate_processed_features


class TestDataSchema:
    """Test suite for data schema contract validation."""

    @pytest.fixture
    def schema_path(self):
        """Load the schema definition file."""
        return Path(__file__).parent.parent.parent / "contracts" / "data_schema.yaml"

    @pytest.fixture
    def schema(self, schema_path):
        """Load and return the schema."""
        with open(schema_path, 'r') as f:
            return yaml.safe_load(f)

    def test_schema_file_exists(self, schema_path):
        """Test that the schema file exists."""
        assert schema_path.exists(), f"Schema file not found at {schema_path}"

    def test_schema_structure(self, schema):
        """Test that the schema has the required top-level sections."""
        required_sections = ['raw_data', 'processed_features', 'candidates', 'verification_requests']
        for section in required_sections:
            assert section in schema, f"Missing section '{section}' in schema"

    def test_raw_data_schema_definition(self, schema):
        """Test raw data schema has required fields."""
        raw_schema = schema['raw_data']
        assert 'required_columns' in raw_schema
        assert 'composition' in raw_schema['required_columns']
        assert 'log10_Rc' in raw_schema['required_columns']

    def test_processed_features_schema_definition(self, schema):
        """Test processed features schema has required fields."""
        proc_schema = schema['processed_features']
        assert 'required_columns' in proc_schema
        assert 'composition' in proc_schema['required_columns']
        assert 'source_row_id' in proc_schema['required_columns']
        assert 'VEC_avg' in proc_schema['required_columns']

    def test_candidates_schema_definition(self, schema):
        """Test candidates schema has required fields."""
        cand_schema = schema['candidates']
        assert 'required_columns' in cand_schema
        assert 'composition' in cand_schema['required_columns']
        assert 'predicted_log10_Rc' in cand_schema['required_columns']
        assert 'novelty_status' in cand_schema['required_columns']

    def test_verification_requests_schema_definition(self, schema):
        """Test verification requests JSON schema has required fields."""
        ver_schema = schema['verification_requests']
        assert 'item_schema' in ver_schema
        item_props = ver_schema['item_schema']['properties']
        assert 'composition' in item_props
        assert 'predicted_log10_Rc' in item_props
        assert 'novelty_status' in item_props
        assert 'status' in item_props

    def test_novelty_status_enum(self, schema):
        """Test that novelty_status has valid enum values."""
        ver_schema = schema['verification_requests']
        novelty_enum = ver_schema['item_schema']['properties']['novelty_status']['enum']
        expected = ['novel', 'known', 'unverified_external']
        assert set(novelty_enum) == set(expected), f"Novelty enum mismatch: {novelty_enum} != {expected}"

    @pytest.mark.integration
    def test_schema_matches_contracts(self, schema):
        """
        Main contract test: validates that the schema definition matches
        the expected structure derived from FR-001, FR-002, FR-006, FR-008.
        This test can run before data download to ensure the schema is correctly defined.
        """
        # Verify all required sections exist
        assert 'raw_data' in schema
        assert 'processed_features' in schema
        assert 'candidates' in schema
        assert 'verification_requests' in schema

        # Verify raw data requirements (FR-001)
        raw_cols = schema['raw_data']['required_columns']
        assert 'composition' in raw_cols
        assert 'log10_Rc' in raw_cols

        # Verify processed features requirements (FR-002)
        proc_cols = schema['processed_features']['required_columns']
        assert 'VEC_avg' in proc_cols
        assert 'atomic_radius_mean' in proc_cols
        assert 'electronegativity_mean' in proc_cols

        # Verify candidates requirements (FR-006)
        cand_cols = schema['candidates']['required_columns']
        assert 'predicted_log10_Rc' in cand_cols
        assert 'novelty_status' in cand_cols
        assert 'final_score' in cand_cols

        # Verify verification requests requirements (FR-008)
        ver_props = schema['verification_requests']['item_schema']['properties']
        assert 'composition' in ver_props
        assert 'confidence_interval' in ver_props
        assert 'status' in ver_props

        assert True, "Schema definition matches contract requirements"

    def test_csv_schema_validator_import(self):
        """Test that the CSV schema validator can be imported and used."""
        # This test ensures the validator module is correctly implemented
        assert callable(validate_csv_schema)
        assert callable(load_schema)
        assert callable(validate_processed_features)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
