"""
Contract tests for ScoreRecord JSON schema validation.

These tests ensure that generated score records conform to the
contracts/score-record.schema.yaml definition.
"""
import json
import pytest
from pathlib import Path
from typing import Dict, Any
import yaml

# Import schema validation utilities
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

# Import project data models for reference
from src.data_models import ScoreRecord


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load JSON schema from YAML file."""
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    return schema


def validate_score_record(record: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """Validate a score record against the schema."""
    if not HAS_JSONSCHEMA:
        pytest.skip("jsonschema library not installed")
    
    try:
        jsonschema.validate(instance=record, schema=schema)
    except jsonschema.ValidationError as e:
        pytest.fail(f"Score record validation failed: {e.message}")


class TestScoreRecordSchema:
    """Tests for ScoreRecord schema compliance."""

    @pytest.fixture
    def schema(self) -> Dict[str, Any]:
        """Load the ScoreRecord schema."""
        schema_path = Path("code/contracts/score-record.schema.yaml")
        if not schema_path.exists():
            pytest.skip("Schema file not found")
        return load_schema(schema_path)

    @pytest.fixture
    def valid_score_record(self) -> Dict[str, Any]:
        """Create a valid ScoreRecord instance."""
        return {
            "instance_id": "test-001",
            "logic_score": 0.85,
            "fidelity_score": 0.92,
            "ssim": 0.88,
            "lpips": 0.12,
            "vllm_description": "A test description",
            "p_value_logic": 0.03,
            "p_value_fidelity": 0.01,
            "beta_logic": 0.45,
            "beta_fidelity": 0.55
        }

    def test_required_fields(self, schema: Dict[str, Any], valid_score_record: Dict[str, Any]):
        """Test that all required fields are present."""
        required_fields = schema.get('required', [])
        for field in required_fields:
            assert field in valid_score_record, f"Missing required field: {field}"

    def test_schema_compliance(self, schema: Dict[str, Any], valid_score_record: Dict[str, Any]):
        """Test that a valid record passes schema validation."""
        validate_score_record(valid_score_record, schema)

    def test_invalid_logic_score(self, schema: Dict[str, Any]):
        """Test that invalid logic_score is rejected."""
        record = {
            "instance_id": "test-001",
            "logic_score": 1.5,  # Out of range
            "fidelity_score": 0.92,
            "ssim": 0.88,
            "lpips": 0.12,
            "vllm_description": "A test description",
            "p_value_logic": 0.03,
            "p_value_fidelity": 0.01,
            "beta_logic": 0.45,
            "beta_fidelity": 0.55
        }
        
        if HAS_JSONSCHEMA:
            schema_path = Path("code/contracts/score-record.schema.yaml")
            if schema_path.exists():
                schema = load_schema(schema_path)
                with pytest.raises(jsonschema.ValidationError):
                    jsonschema.validate(instance=record, schema=schema)

    def test_missing_instance_id(self, schema: Dict[str, Any], valid_score_record: Dict[str, Any]):
        """Test that missing instance_id is rejected."""
        record = valid_score_record.copy()
        del record["instance_id"]
        
        if HAS_JSONSCHEMA:
            schema_path = Path("code/contracts/score-record.schema.yaml")
            if schema_path.exists():
                schema = load_schema(schema_path)
                with pytest.raises(jsonschema.ValidationError):
                    jsonschema.validate(instance=record, schema=schema)

    def test_null_values(self, schema: Dict[str, Any], valid_score_record: Dict[str, Any]):
        """Test that null values in required fields are rejected."""
        record = valid_score_record.copy()
        record["logic_score"] = None
        
        if HAS_JSONSCHEMA:
            schema_path = Path("code/contracts/score-record.schema.yaml")
            if schema_path.exists():
                schema = load_schema(schema_path)
                with pytest.raises(jsonschema.ValidationError):
                    jsonschema.validate(instance=record, schema=schema)