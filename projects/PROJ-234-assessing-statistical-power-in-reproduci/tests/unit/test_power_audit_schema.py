"""
Unit tests for the power_audit_result schema validation logic.
"""
import pytest
import yaml
import os
from pathlib import Path
import sys

# Add code directory to path for imports if running from tests
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.verify_schema import load_and_validate_schema, check_yamllint

class TestPowerAuditSchema:
    @pytest.fixture
    def schema_path(self):
        project_root = Path(__file__).resolve().parent.parent.parent
        return project_root / "contracts" / "power_audit_result.schema.yaml"

    def test_schema_file_exists(self, schema_path):
        """Verify the schema file exists on disk."""
        assert schema_path.exists(), f"Schema file not found at {schema_path}"

    def test_schema_loads_valid_yaml(self, schema_path):
        """Verify the schema is valid YAML."""
        with open(schema_path, 'r') as f:
            data = yaml.safe_load(f)
        assert isinstance(data, dict)
        assert data.get("type") == "object"
        assert "properties" in data
        assert "required" in data

    def test_required_fields_present(self, schema_path):
        """Verify all required fields are defined in properties."""
        with open(schema_path, 'r') as f:
            data = yaml.safe_load(f)
        
        required = set(data.get("required", []))
        properties = set(data.get("properties", {}).keys())
        
        assert required.issubset(properties), f"Missing properties: {required - properties}"

    def test_specific_fields_exist(self, schema_path):
        """Verify specific fields required by US3 exist."""
        with open(schema_path, 'r') as f:
            data = yaml.safe_load(f)
        
        props = data.get("properties", {})
        required_fields = ["dataset_id", "observed_power", "mdes", "threshold_met", "status"]
        
        for field in required_fields:
            assert field in props, f"Required field '{field}' missing from schema properties"

    def test_load_and_validate_function(self, schema_path):
        """Test the helper function loads the schema correctly."""
        try:
            schema = load_and_validate_schema(str(schema_path))
            assert schema is not None
            assert schema["type"] == "object"
        except Exception as e:
            pytest.fail(f"load_and_validate_schema failed: {e}")

    def test_schema_content_integrity(self, schema_path):
        """Verify the schema contains the specific disclaimer about observed power logic."""
        with open(schema_path, 'r') as f:
            content = f.read()
        
        # Check for key descriptions that align with the spec
        assert "observed_power" in content
        assert "mdes" in content
        assert "threshold_met" in content
        assert "clamped" in content.lower() or "0.0" in content or "1.0" in content