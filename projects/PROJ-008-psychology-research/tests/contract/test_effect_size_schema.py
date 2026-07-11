"""
Contract test for effect size schema (US2).

This test validates that the EffectSize Pydantic model conforms to the
schema defined in contracts/effect_size.schema.yaml. It ensures that
serialized data produced by the analysis pipeline matches the expected
structure for downstream consumption and archiving.
"""
import json
import os
import sys
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.models import EffectSize
from code.utils.config import get_output_path


def load_schema(schema_path: str) -> dict:
    """Load a YAML schema file."""
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_model_against_schema(model: EffectSize, schema: dict) -> None:
    """
    Validate a Pydantic model instance against a JSON Schema-like dict.
    
    This is a simplified validation checking for required fields and types
    based on the schema definition.
    """
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    
    model_dict = model.model_dump()
    
    # Check required fields
    missing_fields = set(required) - set(model_dict.keys())
    assert not missing_fields, f"Missing required fields: {missing_fields}"
    
    # Check property types (basic check)
    for field_name, field_schema in properties.items():
        if field_name in model_dict:
            expected_type = field_schema.get("type")
            value = model_dict[field_name]
            
            type_map = {
                "string": str,
                "number": (int, float),
                "integer": int,
                "boolean": bool,
                "array": list,
                "object": dict,
            }
            
            if expected_type and expected_type in type_map:
                assert isinstance(value, type_map[expected_type]), (
                    f"Field '{field_name}' expected {expected_type}, got {type(value)}"
                )


@pytest.fixture
def effect_size_schema():
    """Load the effect_size schema from contracts directory."""
    contracts_dir = project_root / "contracts"
    schema_path = contracts_dir / "effect_size.schema.yaml"
    
    if not schema_path.exists():
        pytest.fail(f"Schema file not found at {schema_path}. "
                    "Ensure T007 (Create schema contracts) is completed first.")
                    
    return load_schema(str(schema_path))


@pytest.fixture
def valid_effect_size_data():
    """Return a dictionary of valid data for an EffectSize model."""
    return {
        "study_id": "NCT01234567",
        "arm_treatment": "Mindfulness-Based Stress Reduction",
        "arm_control": "Waitlist Control",
        "effect_size": 0.45,
        "se_effect_size": 0.12,
        "variance_effect_size": 0.0144,
        "n_treatment": 25,
        "n_control": 25,
        "mean_treatment": 15.2,
        "mean_control": 12.8,
        "sd_treatment": 4.5,
        "sd_control": 4.1,
        "outcome_domain": "Social Responsiveness",
        "timepoint": "post_intervention",
        "hedges_g": 0.42,
        "ci_lower": 0.18,
        "ci_upper": 0.66,
        "study_year": 2023,
    }


def test_effect_size_model_instantiation(valid_effect_size_data):
    """Test that the EffectSize model can be instantiated with valid data."""
    try:
        es = EffectSize(**valid_effect_size_data)
        assert es.study_id == valid_effect_size_data["study_id"]
        assert es.effect_size == valid_effect_size_data["effect_size"]
        assert es.hedges_g is not None
    except ValidationError as e:
        pytest.fail(f"EffectSize model failed validation with valid data: {e}")


def test_effect_size_serialization(valid_effect_size_data, effect_size_schema):
    """Test that serialized EffectSize matches schema requirements."""
    es = EffectSize(**valid_effect_size_data)
    serialized = es.model_dump()
    
    validate_model_against_schema(es, effect_size_schema)
    
    # Verify specific schema constraints if present
    if "properties" in effect_size_schema:
        if "outcome_domain" in effect_size_schema["properties"]:
            # Check if it's an enum in schema
            enum_values = effect_size_schema["properties"]["outcome_domain"].get("enum")
            if enum_values:
                assert serialized["outcome_domain"] in enum_values, \
                    f"Outcome domain {serialized['outcome_domain']} not in allowed values: {enum_values}"


def test_effect_size_missing_required_field(effect_size_schema):
    """Test that missing required fields raise ValidationError."""
    incomplete_data = {
        "study_id": "NCT99999999",
        "arm_treatment": "Intervention",
        # Missing required 'effect_size' and other fields
    }
    
    with pytest.raises(ValidationError):
        EffectSize(**incomplete_data)


def test_effect_size_invalid_type(effect_size_schema):
    """Test that invalid types raise ValidationError."""
    invalid_data = {
        "study_id": "NCT99999999",
        "arm_treatment": "Intervention",
        "arm_control": "Control",
        "effect_size": "not_a_number",  # Should be float
        "se_effect_size": 0.1,
        "variance_effect_size": 0.01,
        "n_treatment": 10,
        "n_control": 10,
        "mean_treatment": 10.0,
        "mean_control": 8.0,
        "sd_treatment": 2.0,
        "sd_control": 2.0,
        "outcome_domain": "Social Responsiveness",
        "timepoint": "post_intervention",
        "hedges_g": 0.5,
        "ci_lower": 0.1,
        "ci_upper": 0.9,
        "study_year": 2023,
    }
    
    with pytest.raises(ValidationError):
        EffectSize(**invalid_data)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
