import json
import yaml
import pytest
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import CONFIG

@pytest.fixture
def schema():
    """Load the output schema."""
    with open(CONFIG.OUTPUT_SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

def test_schema_exists():
    """Test that the output schema file exists."""
    assert CONFIG.OUTPUT_SCHEMA_PATH.exists(), "Output schema file does not exist"

def test_schema_structure(schema):
    """Test that the schema has the required structure."""
    assert '$schema' in schema
    assert 'title' in schema
    assert 'type' in schema
    assert schema['type'] == 'object'
    assert 'required' in schema
    assert 'properties' in schema

def test_required_fields(schema):
    """Test that all required fields are defined."""
    required = schema['required']
    assert 'modeling' in required
    assert 'correlation_analysis' in required
    assert 'interpretability' in required
    assert 'metadata' in required

def test_output_json_conforms_to_schema(schema):
    """Test that the actual output.json conforms to the schema."""
    if not CONFIG.OUTPUT_JSON_PATH.exists():
        pytest.skip("Output JSON file does not exist yet")
    
    with open(CONFIG.OUTPUT_JSON_PATH, 'r') as f:
        output = json.load(f)
    
    # Basic validation
    for field in schema['required']:
        assert field in output, f"Missing required field: {field}"
    
    # Check modeling section
    modeling = output['modeling']
    modeling_required = schema['properties']['modeling']['required']
    for field in modeling_required:
        assert field in modeling, f"Missing modeling field: {field}"
        assert isinstance(modeling[field], (int, float, bool)), \
            f"Modeling field {field} should be a number or boolean"
    
    # Check correlation section
    correlation = output['correlation_analysis']
    correlation_required = schema['properties']['correlation_analysis']['required']
    for field in correlation_required:
        assert field in correlation, f"Missing correlation field: {field}"
    
    # Check interpretability section
    interpretability = output['interpretability']
    interp_required = schema['properties']['interpretability']['required']
    for field in interp_required:
        assert field in interpretability, f"Missing interpretability field: {field}"
    
    # Check metadata section
    metadata = output['metadata']
    meta_required = schema['properties']['metadata']['required']
    for field in meta_required:
        assert field in metadata, f"Missing metadata field: {field}"
        assert isinstance(metadata[field], str), \
            f"Metadata field {field} should be a string"