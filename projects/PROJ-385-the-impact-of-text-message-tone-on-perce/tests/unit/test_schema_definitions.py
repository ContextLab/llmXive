"""
Unit tests for schema definitions.
Ensures that the schema files exist and contain valid YAML structure.
"""
import os
import yaml
import pytest
from pathlib import Path

# Helper to get contract directory
def get_contracts_dir():
    # Assuming tests run from project root or code/
    current_dir = Path(__file__).parent
    # Traverse up to find project root if needed, or assume standard layout
    # Standard layout: tests/unit/ -> ../.. -> specs/...
    base = current_dir.parent.parent
    return base / "specs" / "001-text-tone-emotional-support" / "contracts"

@pytest.fixture
def contracts_dir():
    return get_contracts_dir()

def test_stimulus_schema_exists(contracts_dir):
    schema_path = contracts_dir / "stimulus.schema.yaml"
    assert schema_path.exists(), f"Stimulus schema file not found at {schema_path}"

def test_stimulus_schema_valid_yaml(contracts_dir):
    schema_path = contracts_dir / "stimulus.schema.yaml"
    try:
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        assert isinstance(schema, dict), "Schema must be a dictionary"
        assert 'properties' in schema, "Schema must have 'properties'"
        assert 'required' in schema, "Schema must have 'required'"
    except yaml.YAMLError as e:
        pytest.fail(f"Invalid YAML in stimulus schema: {e}")

def test_stimulus_schema_required_fields(contracts_dir):
    schema_path = contracts_dir / "stimulus.schema.yaml"
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    required_fields = schema.get('required', [])
    expected_fields = ['stimulus_id', 'base_scenario', 'tone_cues', 'cue_intensity', 'text_content', 'generated_at']
    
    for field in expected_fields:
        assert field in required_fields, f"Missing required field '{field}' in stimulus schema"

def test_rating_schema_exists(contracts_dir):
    schema_path = contracts_dir / "rating.schema.yaml"
    assert schema_path.exists(), f"Rating schema file not found at {schema_path}"

def test_rating_schema_valid_yaml(contracts_dir):
    schema_path = contracts_dir / "rating.schema.yaml"
    try:
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        assert isinstance(schema, dict), "Schema must be a dictionary"
        assert 'properties' in schema, "Schema must have 'properties'"
    except yaml.YAMLError as e:
        pytest.fail(f"Invalid YAML in rating schema: {e}")

def test_rating_schema_required_fields(contracts_dir):
    schema_path = contracts_dir / "rating.schema.yaml"
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    required_fields = schema.get('required', [])
    expected_fields = ['rating_id', 'participant_id', 'stimulus_id', 'relationship_context', 
                       'support_score', 'warmth_score', 'competence_score', 'timestamp']
    
    for field in expected_fields:
        assert field in required_fields, f"Missing required field '{field}' in rating schema"

def test_analysis_result_schema_exists(contracts_dir):
    schema_path = contracts_dir / "analysis_result.schema.yaml"
    assert schema_path.exists(), f"Analysis result schema file not found at {schema_path}"

def test_analysis_result_schema_valid_yaml(contracts_dir):
    schema_path = contracts_dir / "analysis_result.schema.yaml"
    try:
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        assert isinstance(schema, dict), "Schema must be a dictionary"
        assert 'properties' in schema, "Schema must have 'properties'"
    except yaml.YAMLError as e:
        pytest.fail(f"Invalid YAML in analysis result schema: {e}")

def test_analysis_result_schema_required_fields(contracts_dir):
    schema_path = contracts_dir / "analysis_result.schema.yaml"
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    required_fields = schema.get('required', [])
    expected_fields = ['analysis_id', 'model_formula', 'fixed_effects', 'variance_components', 
                       'model_fit', 'post_hoc_results', 'generated_at']
    
    for field in expected_fields:
        assert field in required_fields, f"Missing required field '{field}' in analysis result schema"