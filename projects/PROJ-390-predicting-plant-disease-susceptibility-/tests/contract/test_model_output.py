"""
Contract tests for model_output schema (Task T017).

Validates model_performance.json structure.
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

class TestModelOutputSchema:
    """Tests for the model_output.json schema contract."""

    @pytest.fixture
    def schema_path(self):
        return project_root / "data" / "contracts" / "model_output.schema.yaml"

    def test_schema_file_exists(self, schema_path):
        """Verify the model_output schema file exists."""
        assert schema_path.exists(), f"Schema file missing: {schema_path}"

    def test_schema_is_valid_yaml(self, schema_path):
        """Verify the schema file is valid YAML."""
        with open(schema_path, 'r', encoding='utf-8') as f:
            try:
                yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in schema: {e}")

    @pytest.mark.skipif(jsonschema is None, reason="jsonschema not installed")
    def test_required_metrics_present(self, schema_path):
        """Verify the schema requires all required metrics."""
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        
        metrics_required = schema['properties']['metrics']['required']
        assert 'auc_roc' in metrics_required
        assert 'precision' in metrics_required
        assert 'recall' in metrics_required
        assert 'f1_score' in metrics_required

    @pytest.mark.skipif(jsonschema is None, reason="jsonschema not installed")
    def test_auc_roc_range(self, schema_path):
        """Verify AUC-ROC is constrained to [0, 1]."""
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        
        auc_roc_def = schema['properties']['metrics']['properties']['auc_roc']
        assert auc_roc_def['minimum'] == 0
        assert auc_roc_def['maximum'] == 1