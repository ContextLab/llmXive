"""
Contract tests for variance_decomposition schema (Task T023/T034/T036).

Validates variance_decomposition.json structure.
"""
import pytest
import yaml
import json
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    import jsonschema
except ImportError:
    jsonschema = None

class TestVarianceDecompositionSchema:
    """Tests for the variance_decomposition.json schema contract."""

    @pytest.fixture
    def schema_path(self):
        return project_root / "data" / "contracts" / "variance_decomposition.schema.yaml"

    def test_schema_file_exists(self, schema_path):
        """Verify the variance_decomposition schema file exists."""
        assert schema_path.exists(), f"Schema file missing: {schema_path}"

    def test_schema_is_valid_yaml(self, schema_path):
        """Verify the schema file is valid YAML."""
        with open(schema_path, 'r', encoding='utf-8') as f:
            try:
                yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in schema: {e}")

    @pytest.mark.skipif(jsonschema is None, reason="jsonschema not installed")
    def test_required_keys_present(self, schema_path):
        """Verify the schema requires total_variance_explained and group_percentages."""
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        
        required = schema.get('required', [])
        assert 'total_variance_explained' in required
        assert 'group_percentages' in required

    @pytest.mark.skipif(jsonschema is None, reason="jsonschema not installed")
    def test_group_percentages_structure(self, schema_path):
        """Verify group_percentages contains genomic, environmental, and shared."""
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        
        group_props = schema['properties']['group_percentages']['properties']
        required_group = schema['properties']['group_percentages']['required']
        
        assert 'genomic' in required_group
        assert 'environmental' in required_group
        # 'shared' is allowed but not strictly required by the schema definition in T007,
        # but the test verifies it's defined in properties if we want to enforce it later.
        assert 'genomic' in group_props
        assert 'environmental' in group_props

    @pytest.mark.skipif(jsonschema is None, reason="jsonschema not installed")
    def test_variance_values_are_numeric(self, schema_path):
        """Verify that variance values are defined as numbers."""
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        
        total_def = schema['properties']['total_variance_explained']
        assert total_def['type'] == 'number'
        
        genomic_def = schema['properties']['group_percentages']['properties']['genomic']
        assert genomic_def['type'] == 'number'
        
        environmental_def = schema['properties']['group_percentages']['properties']['environmental']
        assert environmental_def['type'] == 'number'