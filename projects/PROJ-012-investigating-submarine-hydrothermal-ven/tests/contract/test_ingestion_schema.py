"""
Contract test for data ingestion schema (T008, T007).

Validates that ingestion pipeline outputs conform to sample_schema.schema.yaml.
"""
import pytest
import pandas as pd
from pathlib import Path
import yaml

BASE_DIR = Path(__file__).parent.parent.parent
CONTRACTS_DIR = BASE_DIR / "contracts"


@pytest.fixture
def sample_schema():
    with open(CONTRACTS_DIR / "sample_schema.schema.yaml", 'r') as f:
        return yaml.safe_load(f)


def test_unified_sample_table_columns(sample_schema):
    """Verify unified sample table has all required columns."""
    # This test validates the expected schema, not actual data
    # Actual data validation happens in integration tests
    required_columns = {
        'sample_id', 'timestamp', 'pH', 'temp', 'pH_sd',
        'location', 'fastq_path', 'deployment_event',
        'sensor_id', 'coordinates'
    }
    schema_columns = set(sample_schema['properties'].keys())

    # All required schema fields should be in the output
    missing = required_columns - schema_columns
    assert not missing, f"Missing columns in schema: {missing}"


def test_ph_outlier_ranges(sample_schema):
    """Verify pH outlier ranges are defined in schema."""
    ph_props = sample_schema['properties']['pH']
    assert 'x-validation-rules' in ph_props, "Missing pH validation rules"
    rules = ph_props['x-validation-rules']
    assert any('OUTLIER' in r for r in rules), "Missing outlier rule"
    assert any('edge range' in r.lower() for r in rules), "Missing edge range rule"


def test_ph_heterogeneity_threshold(sample_schema):
    """Verify pH heterogeneity threshold is defined."""
    ph_sd_props = sample_schema['properties']['pH_sd']
    assert 'x-validation-rules' in ph_sd_props, "Missing pH_sd validation rules"
    rules = ph_sd_props['x-validation-rules']
    assert any('0.2' in r for r in rules), "Missing 0.2 threshold rule"


def test_coordinates_format(sample_schema):
    """Verify coordinates format is validated."""
    coords_props = sample_schema['properties']['coordinates']
    assert 'pattern' in coords_props, "Missing coordinates pattern"
    assert 'lat' in coords_props['description'].lower() or 'lon' in coords_props['description'].lower(), \
        "Missing lat/lon in description"
