"""
Contract test to verify schema files are valid YAML and loadable.
This ensures the schema definitions are syntactically correct.
"""

import pytest
from pathlib import Path
from tests.contract import load_schema, DATASET_SCHEMA_PATH, RESULT_SCHEMA_PATH


class TestSchemaLoadability:
    """Tests to ensure schema files can be loaded."""

    def test_dataset_schema_loads(self):
        """Verify dataset.schema.yaml is valid YAML."""
        schema = load_schema(DATASET_SCHEMA_PATH)
        assert schema is not None
        assert 'type' in schema
        assert schema['type'] == 'object'
        assert 'properties' in schema
        assert 'metadata' in schema['properties']
        assert 'subjects' in schema['properties']

    def test_result_schema_loads(self):
        """Verify result.schema.yaml is valid YAML."""
        schema = load_schema(RESULT_SCHEMA_PATH)
        assert schema is not None
        assert 'type' in schema
        assert schema['type'] == 'object'
        assert 'properties' in schema
        assert 'primary_metrics' in schema['properties']
        assert 'statistical_validation' in schema['properties']
        assert 'sensitivity_analysis' in schema['properties']

    def test_dataset_schema_has_required_fields(self):
        """Verify dataset schema has required top-level fields."""
        schema = load_schema(DATASET_SCHEMA_PATH)
        assert 'required' in schema
        assert 'metadata' in schema['required']
        assert 'subjects' in schema['required']

    def test_result_schema_has_required_fields(self):
        """Verify result schema has required top-level fields."""
        schema = load_schema(RESULT_SCHEMA_PATH)
        assert 'required' in schema
        assert 'metadata' in schema['required']
        assert 'primary_metrics' in schema['required']
        assert 'statistical_validation' in schema['required']

    def test_dataset_metadata_schema(self):
        """Verify dataset metadata structure."""
        schema = load_schema(DATASET_SCHEMA_PATH)
        metadata_props = schema['properties']['metadata']['properties']
        assert 'version' in metadata_props
        assert 'created_at' in metadata_props
        assert 'n_subjects' in metadata_props
        assert 'n_features' in metadata_props

    def test_result_metrics_schema(self):
        """Verify result metrics structure."""
        schema = load_schema(RESULT_SCHEMA_PATH)
        metrics_props = schema['properties']['primary_metrics']['properties']
        assert 'mean_r' in metrics_props
        assert 'mean_r_squared' in metrics_props
        assert 'std_r' in metrics_props
        assert 'std_r_squared' in metrics_props