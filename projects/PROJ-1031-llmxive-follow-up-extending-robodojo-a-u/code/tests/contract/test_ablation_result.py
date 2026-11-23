"""
Contract test for AblationResult schema validation.
"""
import pytest
import sys
from pathlib import Path
import json
import yaml
from jsonschema import validate, ValidationError

# Add src to path if running directly
if "code" not in sys.path:
    code_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(code_root))

SCHEMA_PATH = Path(__file__).parent.parent.parent / "specs" / "001-symbolic-dojo-extend" / "contracts" / "ablation_result.schema.yaml"

class TestAblationResultContract:
    @pytest.fixture
    def schema(self):
        with open(SCHEMA_PATH, "r") as f:
            return yaml.safe_load(f)

    @pytest.fixture
    def valid_result(self):
        return {
            "graph_type": "Full Affordance Graph",
            "success_rate": 0.85,
            "compute_overhead": 12.4
        }

    @pytest.fixture
    def invalid_result_missing_field(self):
        return {
            "graph_type": "Simplified Connectivity Graph",
            "success_rate": 0.90
        }

    @pytest.fixture
    def invalid_result_wrong_type(self):
        return {
            "graph_type": "Test Graph",
            "success_rate": "not a float",
            "compute_overhead": 5.0
        }

    @pytest.fixture
    def invalid_result_out_of_range(self):
        return {
            "graph_type": "Test Graph",
            "success_rate": 1.5,
            "compute_overhead": 5.0
        }

    def test_valid_ablation_result(self, schema, valid_result):
        """Test that a valid AblationResult passes validation."""
        validate(instance=valid_result, schema=schema)

    def test_missing_required_field(self, schema, invalid_result_missing_field):
        """Test that a result missing a required field fails validation."""
        with pytest.raises(ValidationError):
            validate(instance=invalid_result_missing_field, schema=schema)

    def test_wrong_type_field(self, schema, invalid_result_wrong_type):
        """Test that a result with wrong type for success_rate fails validation."""
        with pytest.raises(ValidationError):
            validate(instance=invalid_result_wrong_type, schema=schema)

    def test_out_of_range_success_rate(self, schema, invalid_result_out_of_range):
        """Test that a result with success_rate > 1.0 fails validation."""
        with pytest.raises(ValidationError):
            validate(instance=invalid_result_out_of_range, schema=schema)

    def test_additional_properties_rejected(self, schema, valid_result):
        """Test that additional properties are rejected if strict schema is used."""
        # The schema has additionalProperties: false, so this should fail
        invalid_extra = valid_result.copy()
        invalid_extra["extra_field"] = "should fail"
        with pytest.raises(ValidationError):
            validate(instance=invalid_extra, schema=schema)