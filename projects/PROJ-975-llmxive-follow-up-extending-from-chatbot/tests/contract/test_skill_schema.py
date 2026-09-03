"""
Contract test for T009b: Validate skills.json schema against contracts/skill.schema.yaml.
Ensures that generated skills strictly adhere to the defined JSON Schema.
"""
import json
import os
import pytest
from jsonschema import validate, ValidationError, Draft7Validator

# Path configuration relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCHEMA_PATH = os.path.join(PROJECT_ROOT, "contracts", "skill.schema.yaml")
SKILLS_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "skills.json")

def load_schema():
    """Load the YAML schema file."""
    import yaml
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

def load_sample_skills():
    """Load sample skills if they exist, otherwise return a valid sample object."""
    if os.path.exists(SKILLS_PATH):
        with open(SKILLS_PATH, "r") as f:
            data = json.load(f)
            # Handle both list and dict structures
            if isinstance(data, list) and len(data) > 0:
                return data[0]
            elif isinstance(data, dict):
                return data.get("skills", [{}])[0] if "skills" in data else {}
    return {
        "skill_id": "skill_001",
        "function_code": "def dummy(): pass",
        "embedding_vector": [0.0] * 384,
        "usage_count": 0
    }

class TestSkillSchema:
    @pytest.fixture
    def schema(self):
        return load_schema()

    def test_schema_structure(self, schema):
        """Verify the schema file itself is valid and has required keys."""
        assert "$schema" in schema
        assert "properties" in schema
        assert "skill_id" in schema["properties"]
        assert "function_code" in schema["properties"]
        assert "embedding_vector" in schema["properties"]
        assert "usage_count" in schema["properties"]
        assert "required" in schema
        assert "skill_id" in schema["required"]
        assert "function_code" in schema["required"]
        assert "embedding_vector" in schema["required"]
        assert "usage_count" in schema["required"]

    def test_valid_sample_object(self, schema):
        """Validate a known-good sample object against the schema."""
        sample = {
            "skill_id": "skill_999",
            "function_code": "def add(a, b):\n    return a + b\n",
            "embedding_vector": [0.123] * 384,
            "usage_count": 10
        }
        try:
            validate(instance=sample, schema=schema)
        except ValidationError as e:
            pytest.fail(f"Valid sample failed schema validation: {e.message}")

    def test_invalid_missing_field(self, schema):
        """Ensure validation fails when a required field is missing."""
        invalid_obj = {
            "skill_id": "skill_001",
            "function_code": "def x(): pass",
            "embedding_vector": [0.0] * 384
            # missing usage_count
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_obj, schema=schema)

    def test_invalid_skill_id_format(self, schema):
        """Ensure validation fails if skill_id does not match pattern."""
        invalid_obj = {
            "skill_id": "invalid-id",
            "function_code": "def x(): pass",
            "embedding_vector": [0.0] * 384,
            "usage_count": 0
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_obj, schema=schema)

    def test_invalid_embedding_vector_length(self, schema):
        """Ensure validation fails if embedding_vector is not 384 items."""
        invalid_obj = {
            "skill_id": "skill_001",
            "function_code": "def x(): pass",
            "embedding_vector": [0.0] * 10, # Too short
            "usage_count": 0
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_obj, schema=schema)

    def test_actual_skills_file_validation(self, schema):
        """Validate the actual generated skills.json if it exists."""
        if not os.path.exists(SKILLS_PATH):
            pytest.skip("skills.json not found; skipping actual file validation")
        
        with open(SKILLS_PATH, "r") as f:
            data = json.load(f)
        
        skills_list = data if isinstance(data, list) else data.get("skills", [])
        
        assert len(skills_list) > 0, "skills.json is empty"

        for i, skill in enumerate(skills_list):
            try:
                validate(instance=skill, schema=schema)
            except ValidationError as e:
                pytest.fail(f"Skill at index {i} failed validation: {e.message}")