"""
Unit tests for T007: Data Validation Schemas.
Verifies that the schema files exist, are valid YAML, and contain the required structure.
"""
import os
import sys
import tempfile
from pathlib import Path
import pytest
import yaml

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

SCHEMAS_DIR = PROJECT_ROOT / "specs" / "001-statistical-poll-aggregation" / "contracts"

class TestDatasetSchema:
    def test_schema_file_exists(self):
        """Verify dataset.schema.yaml exists."""
        schema_path = SCHEMAS_DIR / "dataset.schema.yaml"
        assert schema_path.exists(), f"Schema file not found: {schema_path}"

    def test_schema_is_valid_yaml(self):
        """Verify dataset.schema.yaml is valid YAML."""
        schema_path = SCHEMAS_DIR / "dataset.schema.yaml"
        with open(schema_path, 'r') as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in dataset.schema.yaml: {e}")

    def test_schema_has_required_fields(self):
        """Verify dataset.schema.yaml has required top-level keys."""
        schema_path = SCHEMAS_DIR / "dataset.schema.yaml"
        with open(schema_path, 'r') as f:
            data = yaml.safe_load(f)

        required_keys = ["fields", "validation_rules"]
        for key in required_keys:
            assert key in data, f"Missing required key '{key}' in dataset.schema.yaml"

    def test_schema_contains_expected_columns(self):
        """Verify dataset.schema.yaml defines expected columns."""
        schema_path = SCHEMAS_DIR / "dataset.schema.yaml"
        with open(schema_path, 'r') as f:
            data = yaml.safe_load(f)

        expected_columns = ["date", "pollster", "vote_share", "sample_size", "historical_rmse"]
        defined_columns = data.get("fields", {}).keys()

        for col in expected_columns:
            assert col in defined_columns, f"Expected column '{col}' not found in schema"

    def test_validation_rules_present(self):
        """Verify validation rules are defined."""
        schema_path = SCHEMAS_DIR / "dataset.schema.yaml"
        with open(schema_path, 'r') as f:
            data = yaml.safe_load(f)

        rules = data.get("validation_rules", {})
        assert "unique_pollster_date" in rules, "Missing 'unique_pollster_date' rule"
        assert "min_poll_count" in rules, "Missing 'min_poll_count' rule"
        assert "vote_share_range" in rules, "Missing 'vote_share_range' rule"


class TestForecastSchema:
    def test_schema_file_exists(self):
        """Verify forecast.schema.yaml exists."""
        schema_path = SCHEMAS_DIR / "forecast.schema.yaml"
        assert schema_path.exists(), f"Schema file not found: {schema_path}"

    def test_schema_is_valid_yaml(self):
        """Verify forecast.schema.yaml is valid YAML."""
        schema_path = SCHEMAS_DIR / "forecast.schema.yaml"
        with open(schema_path, 'r') as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in forecast.schema.yaml: {e}")

    def test_schema_has_required_fields(self):
        """Verify forecast.schema.yaml has required top-level keys."""
        schema_path = SCHEMAS_DIR / "forecast.schema.yaml"
        with open(schema_path, 'r') as f:
            data = yaml.safe_load(f)

        required_keys = ["fields", "validation_rules"]
        for key in required_keys:
            assert key in data, f"Missing required key '{key}' in forecast.schema.yaml"

    def test_schema_contains_expected_columns(self):
        """Verify forecast.schema.yaml defines expected columns."""
        schema_path = SCHEMAS_DIR / "forecast.schema.yaml"
        with open(schema_path, 'r') as f:
            data = yaml.safe_load(f)

        expected_columns = ["week_bin", "simple_avg_forecast", "weighted_avg_forecast", "ci_lower", "ci_upper"]
        defined_columns = data.get("fields", {}).keys()

        for col in expected_columns:
            assert col in defined_columns, f"Expected column '{col}' not found in schema"

    def test_bayesian_specific_fields(self):
        """Verify Bayesian-specific fields are present."""
        schema_path = SCHEMAS_DIR / "forecast.schema.yaml"
        with open(schema_path, 'r') as f:
            data = yaml.safe_load(f)

        fields = data.get("fields", {})
        assert "bayesian_forecast" in fields, "Missing 'bayesian_forecast' field"
        assert "r_hat" in fields, "Missing 'r_hat' convergence field"

    def test_convergence_rule_present(self):
        """Verify convergence check rule is defined."""
        schema_path = SCHEMAS_DIR / "forecast.schema.yaml"
        with open(schema_path, 'r') as f:
            data = yaml.safe_load(f)

        rules = data.get("validation_rules", {})
        assert "convergence_check" in rules, "Missing 'convergence_check' rule"
        assert rules["convergence_check"]["max_r_hat"] == 1.05, "Incorrect max_r_hat threshold"


class TestSchemaIntegration:
    def test_both_schemas_exist(self):
        """Verify both schema files exist in the contracts directory."""
        dataset_schema = SCHEMAS_DIR / "dataset.schema.yaml"
        forecast_schema = SCHEMAS_DIR / "forecast.schema.yaml"
        assert dataset_schema.exists()
        assert forecast_schema.exists()

    def test_schemas_are_consistent(self):
        """Verify schemas share consistent field definitions where expected."""
        # Load both schemas
        with open(SCHEMAS_DIR / "dataset.schema.yaml", 'r') as f:
            dataset = yaml.safe_load(f)
        with open(SCHEMAS_DIR / "forecast.schema.yaml", 'r') as f:
            forecast = yaml.safe_load(f)

        # Check that 'state' and 'candidate' have consistent definitions
        dataset_state = dataset["fields"].get("state", {})
        forecast_state = forecast["fields"].get("state", {})

        # Both should be strings with pattern ^[A-Z]{2}$
        assert dataset_state.get("type") == "string"
        assert forecast_state.get("type") == "string"
        assert dataset_state.get("pattern") == "^[A-Z]{2}$"
        assert forecast_state.get("pattern") == "^[A-Z]{2}$"