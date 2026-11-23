import os
import yaml
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from schema_generator import generate_dataset_schema, generate_output_schema

class TestDatasetSchema:
    """Contract tests for dataset schema validation."""

    @pytest.fixture
    def schema(self):
        """Load the generated dataset schema."""
        return generate_dataset_schema()

    def test_schema_has_required_properties(self, schema):
        """Test that the schema contains all required properties."""
        required_fields = ["participant_id", "age", "stimulus_type", 
                         "perseverative_errors", "categories_completed"]
        
        for field in required_fields:
            assert field in schema["properties"], f"Missing required field: {field}"

    def test_schema_has_optional_mmse(self, schema):
        """Test that MMSE is defined as optional."""
        assert "MMSE" in schema["properties"], "MMSE field missing"
        # MMSE should not be in required list
        assert "MMSE" not in schema["required"], "MMSE should be optional"

    def test_age_minimum_constraint(self, schema):
        """Test that age has a minimum constraint of 65."""
        age_schema = schema["properties"]["age"]
        assert age_schema["minimum"] == 65, "Age minimum should be 65"

    def test_stimulus_type_enum(self, schema):
        """Test that stimulus_type is constrained to valid values."""
        stimulus_schema = schema["properties"]["stimulus_type"]
        assert stimulus_schema["enum"] == ["nostalgia", "control"]

    def test_schema_valid_json_schema(self, schema):
        """Test that the generated schema is valid JSON Schema."""
        assert "$schema" in schema
        assert "type" in schema
        assert schema["type"] == "object"
