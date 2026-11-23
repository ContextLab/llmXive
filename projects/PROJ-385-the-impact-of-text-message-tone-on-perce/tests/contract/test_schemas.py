"""
Contract Tests for Schema Definitions.
Validates that the schema files are valid YAML and structurally correct.
"""
import pytest
import yaml
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from validate_schemas import load_schema, validate_json_against_schema, validate_csv_against_schema

CONTRACTS_DIR = Path(__file__).parent.parent.parent / 'specs' / '001-text-tone-emotional-support' / 'contracts'

class TestSchemaFiles:
    """Test that schema files exist and are valid YAML."""

    def test_stimulus_schema_exists(self):
        """Verify stimulus.schema.yaml exists."""
        schema_path = CONTRACTS_DIR / 'stimulus.schema.yaml'
        assert schema_path.exists(), f"Schema file missing: {schema_path}"

    def test_stimulus_schema_is_valid_yaml(self):
        """Verify stimulus.schema.yaml is valid YAML."""
        schema_path = CONTRACTS_DIR / 'stimulus.schema.yaml'
        try:
            schema = load_schema(schema_path)
            assert isinstance(schema, dict), "Schema must be a dictionary"
            assert 'type' in schema, "Schema must have 'type' field"
            assert schema['type'] == 'object', "Schema type must be 'object'"
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in stimulus.schema.yaml: {e}")

    def test_rating_schema_exists(self):
        """Verify rating.schema.yaml exists."""
        schema_path = CONTRACTS_DIR / 'rating.schema.yaml'
        assert schema_path.exists(), f"Schema file missing: {schema_path}"

    def test_rating_schema_is_valid_yaml(self):
        """Verify rating.schema.yaml is valid YAML."""
        schema_path = CONTRACTS_DIR / 'rating.schema.yaml'
        try:
            schema = load_schema(schema_path)
            assert isinstance(schema, dict), "Schema must be a dictionary"
            assert 'type' in schema, "Schema must have 'type' field"
            assert schema['type'] == 'object', "Schema type must be 'object'"
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in rating.schema.yaml: {e}")

    def test_analysis_result_schema_exists(self):
        """Verify analysis_result.schema.yaml exists."""
        schema_path = CONTRACTS_DIR / 'analysis_result.schema.yaml'
        assert schema_path.exists(), f"Schema file missing: {schema_path}"

    def test_analysis_result_schema_is_valid_yaml(self):
        """Verify analysis_result.schema.yaml is valid YAML."""
        schema_path = CONTRACTS_DIR / 'analysis_result.schema.yaml'
        try:
            schema = load_schema(schema_path)
            assert isinstance(schema, dict), "Schema must be a dictionary"
            assert 'type' in schema, "Schema must have 'type' field"
            assert schema['type'] == 'object', "Schema type must be 'object'"
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in analysis_result.schema.yaml: {e}")

class TestSchemaProperties:
    """Test that schemas define required properties."""

    def test_stimulus_schema_has_required_properties(self):
        """Verify stimulus schema has all required properties."""
        schema = load_schema(CONTRACTS_DIR / 'stimulus.schema.yaml')
        required = schema.get('required', [])
        properties = schema.get('properties', {})
        
        expected_properties = ['id', 'text', 'emoji_count', 'punctuation_type', 'length_category']
        for prop in expected_properties:
            assert prop in required, f"Property '{prop}' must be required in stimulus schema"
            assert prop in properties, f"Property '{prop}' must be defined in stimulus schema"

    def test_rating_schema_has_required_properties(self):
        """Verify rating schema has all required properties."""
        schema = load_schema(CONTRACTS_DIR / 'rating.schema.yaml')
        required = schema.get('required', [])
        properties = schema.get('properties', {})
        
        expected_properties = ['participant_id', 'stimulus_id', 'relationship', 'rating']
        for prop in expected_properties:
            assert prop in required, f"Property '{prop}' must be required in rating schema"
            assert prop in properties, f"Property '{prop}' must be defined in rating schema"

    def test_rating_schema_relationship_enum(self):
        """Verify rating schema relationship field has correct enum."""
        schema = load_schema(CONTRACTS_DIR / 'rating.schema.yaml')
        relationship_def = schema['properties']['relationship']
        assert 'enum' in relationship_def, "Relationship field must have enum constraint"
        assert 'friend' in relationship_def['enum'], "Enum must include 'friend'"
        assert 'acquaintance' in relationship_def['enum'], "Enum must include 'acquaintance'"

    def test_rating_schema_rating_range(self):
        """Verify rating schema rating field has correct range."""
        schema = load_schema(CONTRACTS_DIR / 'rating.schema.yaml')
        rating_def = schema['properties']['rating']
        assert 'minimum' in rating_def, "Rating field must have minimum"
        assert 'maximum' in rating_def, "Rating field must have maximum"
        assert rating_def['minimum'] == 1, "Minimum rating must be 1"
        assert rating_def['maximum'] == 7, "Maximum rating must be 7"

    def test_analysis_result_schema_has_required_properties(self):
        """Verify analysis result schema has all required properties."""
        schema = load_schema(CONTRACTS_DIR / 'analysis_result.schema.yaml')
        required = schema.get('required', [])
        properties = schema.get('properties', {})
        
        expected_properties = ['model_id', 'fixed_effects', 'random_effects', 'p_values', 'exclusion_summary']
        for prop in expected_properties:
            assert prop in required, f"Property '{prop}' must be required in analysis result schema"
            assert prop in properties, f"Property '{prop}' must be defined in analysis result schema"

class TestSchemaValidationLogic:
    """Test the validation functions against sample data."""

    def test_validate_stimulus_data(self):
        """Test validation against a valid stimulus record."""
        schema = load_schema(CONTRACTS_DIR / 'stimulus.schema.yaml')
        valid_data = {
            'id': 'S001',
            'text': 'Hey, how are you?',
            'emoji_count': 1,
            'punctuation_type': '?',
            'length_category': 'short'
        }
        errors = validate_json_against_schema(valid_data, schema)
        assert len(errors) == 0, f"Valid data should not produce errors: {errors}"

    def test_validate_invalid_stimulus_data(self):
        """Test validation against an invalid stimulus record."""
        schema = load_schema(CONTRACTS_DIR / 'stimulus.schema.yaml')
        invalid_data = {
            'id': 'S001',
            'text': 'Hey',
            'emoji_count': 'two',  # Should be integer
            'punctuation_type': '?',
            'length_category': 'short'
        }
        errors = validate_json_against_schema(invalid_data, schema)
        assert len(errors) > 0, "Invalid data should produce errors"
        assert any('emoji_count' in e for e in errors), "Should flag emoji_count type error"

    def test_validate_rating_data(self):
        """Test validation against a valid rating record."""
        schema = load_schema(CONTRACTS_DIR / 'rating.schema.yaml')
        valid_data = {
            'participant_id': 'PABCD1234',
            'stimulus_id': 'S001',
            'relationship': 'friend',
            'rating': 5
        }
        errors = validate_json_against_schema(valid_data, schema)
        assert len(errors) == 0, f"Valid data should not produce errors: {errors}"

    def test_validate_invalid_rating_relationship(self):
        """Test validation against invalid relationship enum."""
        schema = load_schema(CONTRACTS_DIR / 'rating.schema.yaml')
        invalid_data = {
            'participant_id': 'PABCD1234',
            'stimulus_id': 'S001',
            'relationship': 'stranger',  # Invalid enum
            'rating': 5
        }
        errors = validate_json_against_schema(invalid_data, schema)
        assert len(errors) > 0, "Invalid enum should produce errors"
        assert any('relationship' in e for e in errors), "Should flag relationship enum error"

    def test_validate_invalid_rating_range(self):
        """Test validation against rating outside range."""
        schema = load_schema(CONTRACTS_DIR / 'rating.schema.yaml')
        invalid_data = {
            'participant_id': 'PABCD1234',
            'stimulus_id': 'S001',
            'relationship': 'friend',
            'rating': 10  # Out of 1-7 range
        }
        errors = validate_json_against_schema(invalid_data, schema)
        assert len(errors) > 0, "Out of range value should produce errors"
        assert any('rating' in e for e in errors), "Should flag rating range error"