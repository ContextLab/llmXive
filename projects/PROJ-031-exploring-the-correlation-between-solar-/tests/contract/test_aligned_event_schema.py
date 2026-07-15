"""
Test suite for validating the aligned_event.schema.yaml structure.
Ensures the schema is valid YAML and defines expected fields.
"""
import yaml
import os
import pytest

@pytest.fixture
def schema_path():
    return os.path.join(os.path.dirname(__file__), '..', '..', 'contracts', 'aligned_event.schema.yaml')

@pytest.fixture
def schema(schema_path):
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def test_schema_exists_and_loads(schema_path):
    """Verify the schema file exists and is valid YAML."""
    assert os.path.exists(schema_path), f"Schema file not found at {schema_path}"
    with open(schema_path, 'r') as f:
        data = yaml.safe_load(f)
        assert data is not None

def test_schema_has_required_top_level_keys(schema):
    """Verify standard JSON Schema keys are present."""
    assert '$schema' in schema
    assert 'title' in schema
    assert 'type' in schema
    assert schema['type'] == 'object'
    assert 'properties' in schema
    assert 'required' in schema

def test_schema_defines_aligned_event_id(schema):
    """Verify the primary ID field is defined."""
    assert 'aligned_event_id' in schema['properties']
    assert schema['properties']['aligned_event_id']['type'] == 'string'

def test_schema_defines_flare_event(schema):
    """Verify the nested flare_event structure."""
    assert 'flare_event' in schema['properties']
    flare_props = schema['properties']['flare_event']['properties']
    assert 'flux_peak_w1' in flare_props
    assert 'flux_peak_w2' in flare_props
    assert 'peak_time' in flare_props

def test_schema_defines_cme_event(schema):
    """Verify the nested cme_event structure."""
    assert 'cme_event' in schema['properties']
    cme_props = schema['properties']['cme_event']['properties']
    assert 'speed_km_s' in cme_props
    assert 'angular_width_deg' in cme_props
    # Check that speed allows null for missing data
    speed_type = cme_props['speed_km_s']['type']
    assert speed_type == ['number', 'null'] or speed_type == 'number'

def test_schema_defines_geomagnetic_storm(schema):
    """Verify the nested geomagnetic_storm structure."""
    assert 'geomagnetic_storm' in schema['properties']
    storm_props = schema['properties']['geomagnetic_storm']['properties']
    assert 'dst_min' in storm_props
    assert 'dst_min_time' in storm_props
    assert 'kp_max' in storm_props

def test_schema_handles_missing_predictors(schema):
    """Verify the schema tracks missing data flags."""
    assert 'missing_solar_predictors' in schema['properties']
    assert schema['properties']['missing_solar_predictors']['type'] == 'array'

def test_schema_allows_recurrent_flag(schema):
    """Verify the is_recurrent flag is present in the storm object."""
    storm_props = schema['properties']['geomagnetic_storm']['properties']
    assert 'is_recurrent' in storm_props
    assert storm_props['is_recurrent']['type'] == 'boolean'

def test_schema_no_extra_properties(schema):
    """Ensure strict schema enforcement."""
    assert schema.get('additionalProperties') == False, "Schema should forbid additional properties at root level"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])