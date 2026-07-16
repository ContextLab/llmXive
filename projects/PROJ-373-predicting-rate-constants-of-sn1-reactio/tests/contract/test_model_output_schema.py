import os
import yaml
import pytest
import json
from pathlib import Path
from jsonschema import validate, ValidationError

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_DIR = PROJECT_ROOT / "specs" / "001-predict-sn1-rate-constants" / "contracts"

def load_schema(schema_name: str) -> dict:
    """Load a JSON/YAML schema from the contracts directory."""
    schema_path = SCHEMA_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        if schema_path.suffix in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        elif schema_path.suffix == '.json':
            return json.load(f)
    raise ValueError(f"Unsupported schema format: {schema_path.suffix}")

class TestModelOutputSchema:
    """Contract tests for the model output schema."""

    @pytest.fixture
    def model_schema(self):
        return load_schema("model_output.schema.yaml")

    def test_schema_structure(self, model_schema):
        """Ensure the schema has correct root structure."""
        assert model_schema["type"] == "object"
        assert "required" in model_schema
        assert "model_id" in model_schema["required"]
        assert "metrics" in model_schema["required"]

    def test_metrics_nested_structure(self, model_schema):
        """Verify metrics property exists and has expected sub-properties."""
        props = model_schema["properties"]
        assert "metrics" in props
        assert "properties" in props["metrics"]
        
        metric_props = props["metrics"]["properties"]
        assert "r2" in metric_props
        assert "mae" in metric_props
        assert metric_props["r2"]["type"] == "number"
        assert metric_props["mae"]["type"] == "number"

    def test_validate_sample_output(self, model_schema):
        """Validate a sample model output dictionary."""
        sample_output = {
            "model_id": "test-model-001",
            "hyperparameters": {
                "learning_rate": 0.01,
                "layers": 3
            },
            "metrics": {
                "r2": 0.85,
                "mae": 0.12
            },
            "weights_path": "artifacts/best_model.pt"
        }
        
        try:
            validate(instance=sample_output, schema=model_schema)
        except ValidationError as e:
            pytest.fail(f"Sample output failed schema validation: {e.message}")
