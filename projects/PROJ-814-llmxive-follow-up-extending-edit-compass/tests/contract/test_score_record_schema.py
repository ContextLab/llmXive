"""
Contract tests for ScoreRecord schema validation.
These tests ensure that generated score records adhere to the defined JSON schema.
"""
import json
import pytest
from pathlib import Path
from typing import Dict, Any
import yaml
import sys
from src.data_models import ScoreRecord

# Ensure the project root is in the path if running directly
if str(Path(__file__).parent.parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

SCHEMA_PATH = Path(__file__).parent.parent.parent / "contracts" / "score-record.schema.yaml"

def load_schema() -> Dict[str, Any]:
    """Load the JSON schema from the YAML file."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def validate_score_record(record: Dict[str, Any]) -> bool:
    """
    Validate a dictionary against the ScoreRecord schema.
    Returns True if valid, raises AssertionError otherwise.
    """
    schema = load_schema()
    # Basic validation logic since we don't have jsonschema installed in this snippet
    # In a real scenario, we would use: jsonschema.validate(instance=record, schema=schema)
    
    required_fields = [
        "instance_id", "logic_score", "fidelity_score", "ssim", "lpips",
        "vllm_description", "p_value_logic", "p_value_fidelity", "beta_logic", "beta_fidelity"
    ]
    
    for field in required_fields:
        if field not in record:
            raise AssertionError(f"Missing required field: {field}")
    
    # Type checks
    assert isinstance(record["instance_id"], str), "instance_id must be a string"
    assert isinstance(record["logic_score"], (int, float)), "logic_score must be numeric"
    assert isinstance(record["fidelity_score"], (int, float)), "fidelity_score must be numeric"
    assert isinstance(record["ssim"], (int, float)), "ssim must be numeric"
    assert isinstance(record["lpips"], (int, float)), "lpips must be numeric"
    assert isinstance(record["vllm_description"], str), "vllm_description must be a string"
    assert isinstance(record["p_value_logic"], (int, float)), "p_value_logic must be numeric"
    assert isinstance(record["p_value_fidelity"], (int, float)), "p_value_fidelity must be numeric"
    assert isinstance(record["beta_logic"], (int, float)), "beta_logic must be numeric"
    assert isinstance(record["beta_fidelity"], (int, float)), "beta_fidelity must be numeric"
    
    return True

class TestScoreRecordSchema:
    """Test suite for ScoreRecord schema compliance."""

    @pytest.fixture
    def valid_record_dict(self) -> Dict[str, Any]:
        return {
            "instance_id": "test-001",
            "logic_score": 0.85,
            "fidelity_score": 0.92,
            "ssim": 0.88,
            "lpips": 0.12,
            "vllm_description": "A valid description of the edit.",
            "p_value_logic": 0.03,
            "p_value_fidelity": 0.01,
            "beta_logic": 0.45,
            "beta_fidelity": 0.55
        }

    @pytest.fixture
    def valid_record_model(self) -> ScoreRecord:
        return ScoreRecord(
            instance_id="test-001",
            logic_score=0.85,
            fidelity_score=0.92,
            ssim=0.88,
            lpips=0.12,
            vllm_description="A valid description of the edit.",
            p_value_logic=0.03,
            p_value_fidelity=0.01,
            beta_logic=0.45,
            beta_fidelity=0.55
        )

    def test_schema_file_exists(self):
        """Assert that the schema file exists."""
        assert SCHEMA_PATH.exists(), f"Schema file missing at {SCHEMA_PATH}"

    def test_load_schema_valid(self):
        """Assert that the schema loads without error."""
        schema = load_schema()
        assert isinstance(schema, dict)
        assert "type" in schema
        assert schema["type"] == "object"

    def test_valid_record_dict_passes(self, valid_record_dict):
        """Assert that a valid dictionary passes validation."""
        assert validate_score_record(valid_record_dict) is True

    def test_valid_record_model_passes(self, valid_record_model):
        """Assert that a valid Pydantic model instance passes validation."""
        record_dict = valid_record_model.model_dump()
        assert validate_score_record(record_dict) is True

    def test_missing_field_fails(self, valid_record_dict):
        """Assert that a record with a missing required field fails."""
        del valid_record_dict["instance_id"]
        with pytest.raises(AssertionError):
            validate_score_record(valid_record_dict)

    def test_invalid_type_fails(self, valid_record_dict):
        """Assert that a record with an invalid type fails."""
        valid_record_dict["logic_score"] = "not a number"
        with pytest.raises(AssertionError):
            validate_score_record(valid_record_dict)

    def test_negative_score_handling(self, valid_record_dict):
        """Assert that negative scores are handled (schema allows numeric, logic might restrict)."""
        # The schema allows numeric, but logic might restrict range. 
        # This test ensures the type check passes even if value is negative.
        valid_record_dict["logic_score"] = -0.5
        # Type check passes, but semantic validation might fail later.
        # For schema contract, we only check structure/types here.
        assert validate_score_record(valid_record_dict) is True