import pytest
import json
from pathlib import Path
import jsonschema
import yaml

def load_schema(schema_path):
    """Load a YAML schema file."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def test_model_output_schema_validation():
    """
    T014: Verify model_results.json matches the schema defined in T005b.
    Depends on T005b (schema) and T015 (model_results.json generation).
    """
    model_output_path = Path("data/outputs/model_results.json")
    schema_path = Path("specs/001-predict-carbon-diffusion-bcc/contracts/model_output.schema.yaml")
    
    if not model_output_path.exists():
        pytest.skip("Model output not yet generated. Run 03_train.py first.")
    
    if not schema_path.exists():
        pytest.fail(f"Schema file missing: {schema_path}")
    
    # Load schema
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    # Load data
    with open(model_output_path, 'r') as f:
        data = json.load(f)
    
    # Validate
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        pytest.fail(f"Validation error: {e.message}")

def test_feature_importance_schema_validation():
    """
    T018: Verify feature_importance.json matches its schema.
    """
    feature_importance_path = Path("data/outputs/feature_importance.json")
    
    if not feature_importance_path.exists():
        pytest.skip("Feature importance not yet generated. Run 04_evaluate.py first.")
    
    with open(feature_importance_path, 'r') as f:
        data = json.load(f)
    
    # Basic structural check
    assert 'ranked_features' in data, "ranked_features key missing."
    assert 'top_two' in data, "top_two key missing."
    
    assert isinstance(data['ranked_features'], list), "ranked_features must be a list."
    assert isinstance(data['top_two'], list), "top_two must be a list."
    assert len(data['top_two']) == 2, "top_two must contain exactly two items."
