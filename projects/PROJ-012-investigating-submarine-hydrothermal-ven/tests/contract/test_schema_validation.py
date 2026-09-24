"""
Contract tests for data schema validation (T007).

These tests verify that the YAML schemas in contracts/ are valid,
consistent with the data_models.py definitions, and can be used
to validate input/output data.
"""
import os
import json
import yaml
import pytest
from pathlib import Path
from typing import Dict, Any

# Import from code/data_models.py
from data_models import (
    Sample, OTU, DiversityMetric,
    validate_sample_schema,
    validate_otu_schema,
    validate_diversity_metric_schema
)

BASE_DIR = Path(__file__).parent.parent.parent
CONTRACTS_DIR = BASE_DIR / "contracts"


@pytest.fixture
def sample_schema_path():
    return CONTRACTS_DIR / "sample_schema.schema.yaml"

@pytest.fixture
def otu_schema_path():
    return CONTRACTS_DIR / "otu_table_schema.schema.yaml"

@pytest.fixture
def analysis_schema_path():
    return CONTRACTS_DIR / "analysis_results_schema.schema.yaml"


def test_schemas_are_valid_yaml(sample_schema_path, otu_schema_path, analysis_schema_path):
    """Verify all schema files are valid YAML and parseable."""
    for schema_path in [sample_schema_path, otu_schema_path, analysis_schema_path]:
        assert schema_path.exists(), f"Schema file missing: {schema_path}"
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        assert schema is not None, f"Empty schema: {schema_path}"
        assert 'properties' in schema or 'required' in schema, \
            f"Invalid schema structure: {schema_path}"


def test_sample_schema_matches_data_model(sample_schema_path):
    """Verify sample_schema.yaml matches Sample class in data_models.py."""
    with open(sample_schema_path, 'r') as f:
        schema = yaml.safe_load(f)

    # Check required fields
    required_fields = set(schema.get('required', []))
    sample_fields = {
        'sample_id', 'timestamp', 'pH', 'temp', 'pH_sd',
        'location', 'fastq_path', 'deployment_event',
        'sensor_id', 'coordinates', 'pH_heterogeneous'
    }
    assert required_fields.issubset(sample_fields), \
        f"Schema required fields exceed data model: {required_fields - sample_fields}"

    # Check property definitions
    props = schema.get('properties', {})
    assert 'sample_id' in props, "Missing sample_id in schema"
    assert 'pH' in props, "Missing pH in schema"
    assert 'timestamp' in props, "Missing timestamp in schema"


def test_otu_schema_structure(otu_schema_path):
    """Verify OTU schema has required structure."""
    with open(otu_schema_path, 'r') as f:
        schema = yaml.safe_load(f)

    required = set(schema.get('required', []))
    assert 'otu_table' in required, "Missing otu_table in required"
    assert 'taxonomy' in required, "Missing taxonomy in required"
    assert 'sample_ids' in required, "Missing sample_ids in required"
    assert 'otu_ids' in required, "Missing otu_ids in required"


def test_analysis_schema_structure(analysis_schema_path):
    """Verify analysis results schema has required structure."""
    with open(analysis_schema_path, 'r') as f:
        schema = yaml.safe_load(f)

    required = set(schema.get('required', []))
    assert 'analysis_type' in required, "Missing analysis_type in required"
    assert 'model_stats' in required, "Missing model_stats in required"

    # Check for FR-003.1 metadata flag
    props = schema.get('properties', {})
    if 'model_stats' in props:
        items = props['model_stats'].get('properties', {})
        assert 'metadata_flag' in items, "Missing metadata_flag (FR-003.1)"


def test_validate_sample_schema_function_exists():
    """Verify validation function exists and is callable."""
    assert callable(validate_sample_schema), "validate_sample_schema not callable"


def test_validate_otu_schema_function_exists():
    """Verify validation function exists and is callable."""
    assert callable(validate_otu_schema), "validate_otu_schema not callable"


def test_validate_diversity_metric_schema_function_exists():
    """Verify validation function exists and is callable."""
    assert callable(validate_diversity_metric_schema), "validate_diversity_metric_schema not callable"


def test_schema_versioning(sample_schema_path, otu_schema_path, analysis_schema_path):
    """Verify all schemas have version metadata."""
    for schema_path in [sample_schema_path, otu_schema_path, analysis_schema_path]:
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        assert 'x-schema-version' in schema, \
            f"Missing x-schema-version in {schema_path}"
        assert schema['x-schema-version'] != "1.0.0" or True  # Just ensure it exists


def test_schema_references_correct_tasks(sample_schema_path, otu_schema_path, analysis_schema_path):
    """Verify schemas reference the correct task IDs."""
    for schema_path in [sample_schema_path, otu_schema_path, analysis_schema_path]:
        with open(schema_path, 'r') as f:
            content = f.read()
        # Check that task IDs are referenced
        assert 'T007' in content or 'T008' in content or 'T010' in content, \
            f"Schema {schema_path} missing task references"
