import json
import pytest
import yaml
from pathlib import Path
import jsonschema

def load_schema():
    schema_path = Path("contracts/output.schema.yaml")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def test_schema_exists():
    schema_path = Path("contracts/output.schema.yaml")
    assert schema_path.exists(), "contracts/output.schema.yaml does not exist"

def test_schema_structure():
    schema = load_schema()
    assert '$schema' in schema
    assert schema['$schema'] == "http://json-schema.org/draft-07/schema#"
    assert 'properties' in schema
    assert 'metrics' in schema['properties']
    assert 'shap_analysis' in schema['properties']

def test_metrics_schema():
    schema = load_schema()
    metrics_def = schema['properties']['metrics']
    assert metrics_def['type'] == 'object'
    required = metrics_def.get('required', [])
    assert 'balanced_accuracy' in required
    assert 'roc_auc' in required
    assert 'permutation_p_value' in required
    assert 'framing' in required

def test_shap_analysis_schema():
    schema = load_schema()
    shap_def = schema['properties']['shap_analysis']
    assert shap_def['type'] == 'object'
    required = shap_def.get('required', [])
    assert 'correlations' in required
    assert 'framing' in required

def test_schema_validates_real_data():
    """
    Validates that a sample output matching the expected structure (from T024/T020)
    conforms to the schema.
    """
    schema = load_schema()
    
    sample_data = {
        "metrics": {
            "balanced_accuracy": 0.85,
            "roc_auc": 0.92,
            "permutation_p_value": 0.001,
            "framing": "These results represent associations, not causation"
        },
        "shap_analysis": {
            "correlations": [
                {
                    "feature_name": "InChIKey1",
                    "correlation": 0.65,
                    "p_value": 0.0001,
                    "fdr_corrected_p": 0.0005
                }
            ],
            "collinearity_vif": [
                {
                    "feature_name": "InChIKey1",
                    "vif_value": 1.2
                }
            ],
            "framing": "These results represent associations, not causation"
        }
    }

    try:
        jsonschema.validate(instance=sample_data, schema=schema)
        assert True
    except jsonschema.exceptions.ValidationError as e:
        pytest.fail(f"Sample data failed schema validation: {e.message}")
