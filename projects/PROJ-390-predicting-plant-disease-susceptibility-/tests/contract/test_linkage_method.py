"""
Contract tests for linkage_method schema (Task T015b).

Specifically validates the structure of linkage_method.yaml produced by T015.
"""
import pytest
import yaml
import os
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    import jsonschema
except ImportError:
    jsonschema = None

class TestLinkageMethodSchema:
    """Tests for the linkage_method.yaml schema contract."""

    @pytest.fixture
    def schema_path(self):
        return project_root / "data" / "contracts" / "linkage_method.schema.yaml"

    def test_schema_file_exists(self, schema_path):
        """Verify the linkage_method schema file exists."""
        assert schema_path.exists(), f"Schema file missing: {schema_path}"

    def test_schema_is_valid_yaml(self, schema_path):
        """Verify the schema file is valid YAML."""
        with open(schema_path, 'r', encoding='utf-8') as f:
            try:
                yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in schema: {e}")

    @pytest.mark.skipif(jsonschema is None, reason="jsonschema not installed")
    def test_required_fields_present(self, schema_path):
        """Verify the schema requires the correct fields."""
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        
        required_fields = schema.get('required', [])
        assert 'method_name' in required_fields
        assert 'source_type' in required_fields
        assert 'validation_status' in required_fields
        assert 'timestamp' in required_fields

    @pytest.mark.skipif(jsonschema is None, reason="jsonschema not installed")
    def test_enum_values_correct(self, schema_path):
        """Verify enum values match spec requirements."""
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        
        properties = schema['properties']
        
        # Check source_type enum
        source_type_enum = properties['source_type']['enum']
        assert 'field-trial-db' in source_type_enum
        assert 'pathology-archive' in source_type_enum
        
        # Check validation_status enum
        status_enum = properties['validation_status']['enum']
        assert 'verified' in status_enum
        assert 'ambiguous' in status_enum
        assert 'excluded' in status_enum

    @pytest.mark.skipif(jsonschema is None, reason="jsonschema not installed")
    def test_schema_validates_example(self, schema_path):
        """Test that a valid example passes schema validation."""
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        
        example = {
            "method_name": "independent_phenotype_verification",
            "source_type": "field-trial-db",
            "validation_status": "verified",
            "timestamp": "2024-01-01T12:00:00Z",
            "excluded_samples_count": 0,
            "total_samples_processed": 100
        }
        
        jsonschema.validate(instance=example, schema=schema)

    @pytest.mark.skipif(jsonschema is None, reason="jsonschema not installed")
    def test_schema_rejects_invalid_source_type(self, schema_path):
        """Test that invalid source_type fails validation."""
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        
        invalid_example = {
            "method_name": "independent_phenotype_verification",
            "source_type": "invalid-source",
            "validation_status": "verified",
            "timestamp": "2024-01-01T12:00:00Z",
            "excluded_samples_count": 0,
            "total_samples_processed": 100
        }
        
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=invalid_example, schema=schema)

    @pytest.mark.skipif(jsonschema is None, reason="jsonschema not installed")
    def test_schema_rejects_missing_required_field(self, schema_path):
        """Test that missing required field fails validation."""
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        
        invalid_example = {
            "method_name": "independent_phenotype_verification",
            "validation_status": "verified",
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=invalid_example, schema=schema)