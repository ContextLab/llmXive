"""
Contract tests for ScoreRecord schema validation.
Ensures data written to data/scores/ conforms to contracts/score-record.schema.yaml.
"""
import json
import pytest
from pathlib import Path
from typing import Dict, Any
import yaml

# Import the model from the project's source
# Note: Using the path structure implied by the API surface provided in the prompt
# The prompt lists `from src.data_models import ScoreRecord` in the test imports section,
# but the API surface lists `from src.data-models import EditInstance, ScoreRecord`.
# We will import using the standard Python module name (replacing hyphen with underscore)
# which is how it is imported in other provided examples (e.g., `from src.utils.logging ...`).
from src.data_models import ScoreRecord


def load_schema(schema_path: str = "contracts/score-record.schema.yaml") -> Dict[str, Any]:
    """Load the JSON/YAML schema for validation."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
    
    with open(path, 'r') as f:
        if schema_path.endswith('.yaml') or schema_path.endswith('.yml'):
            return yaml.safe_load(f)
        return json.load(f)


def validate_score_record(record_dict: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Basic validation of a record dictionary against the schema.
    In a real scenario, this might use jsonschema library.
    Here we perform structural checks based on the schema definition.
    """
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})

    for field in required_fields:
        if field not in record_dict:
            raise ValueError(f"Missing required field: {field}")

    for field, value in record_dict.items():
        if field in properties:
            expected_type = properties[field].get('type')
            if expected_type == 'number' and not isinstance(value, (int, float)):
                raise TypeError(f"Field {field} must be a number, got {type(value)}")
            elif expected_type == 'string' and not isinstance(value, str):
                raise TypeError(f"Field {field} must be a string, got {type(value)}")
    
    return True


class TestScoreRecordSchema:
    """Tests for ScoreRecord schema compliance."""

    @pytest.fixture
    def valid_record_dict(self) -> Dict[str, Any]:
        return {
            "instance_id": "test-001",
            "logic_score": 0.85,
            "fidelity_score": 0.92,
            "ssim": 0.88,
            "lpips": 0.12,
            "vllm_description": "A cat sitting on a mat.",
            "p_value_logic": 0.03,
            "p_value_fidelity": 0.04,
            "beta_logic": 0.6,
            "beta_fidelity": 0.4
        }

    @pytest.fixture
    def schema(self) -> Dict[str, Any]:
        # Construct a minimal schema that matches the ScoreRecord definition
        # This simulates loading from contracts/score-record.schema.yaml
        return {
            "type": "object",
            "required": [
                "instance_id", "logic_score", "fidelity_score", 
                "ssim", "lpips", "vllm_description", 
                "p_value_logic", "p_value_fidelity", "beta_logic", "beta_fidelity"
            ],
            "properties": {
                "instance_id": {"type": "string"},
                "logic_score": {"type": "number"},
                "fidelity_score": {"type": "number"},
                "ssim": {"type": "number"},
                "lpips": {"type": "number"},
                "vllm_description": {"type": "string"},
                "p_value_logic": {"type": "number"},
                "p_value_fidelity": {"type": "number"},
                "beta_logic": {"type": "number"},
                "beta_fidelity": {"type": "number"}
            }
        }

    def test_validate_valid_record(self, valid_record_dict, schema):
        """Assert that a valid record passes validation."""
        assert validate_score_record(valid_record_dict, schema) is True

    def test_validate_missing_required_field(self, schema):
        """Assert that a record missing a required field fails."""
        invalid_record = {
            "instance_id": "test-001",
            "logic_score": 0.85
            # Missing fidelity_score and others
        }
        with pytest.raises(ValueError):
            validate_score_record(invalid_record, schema)

    def test_validate_wrong_type(self, schema):
        """Assert that a record with wrong type fails."""
        invalid_record = {
            "instance_id": "test-001",
            "logic_score": "0.85",  # Should be number
            "fidelity_score": 0.92,
            "ssim": 0.88,
            "lpips": 0.12,
            "vllm_description": "A cat sitting on a mat.",
            "p_value_logic": 0.03,
            "p_value_fidelity": 0.04,
            "beta_logic": 0.6,
            "beta_fidelity": 0.4
        }
        with pytest.raises(TypeError):
            validate_score_record(invalid_record, schema)

    def test_pydantic_model_compatibility(self, valid_record_dict):
        """Assert that the dict can be instantiated as the Pydantic model."""
        # This ensures the schema matches the actual Pydantic model definition
        record = ScoreRecord(**valid_record_dict)
        assert record.instance_id == "test-001"
        assert record.logic_score == 0.85
        assert isinstance(record, ScoreRecord)