"""
Unit tests for schema validation logic.
Tests T010: Verify that generated schema files are valid and can be loaded.
"""
import pytest
import yaml
from pathlib import Path
import json

# Import the validator from the project
from utils.schema_validator import load_schema, validate_artifact

# Base path for contracts
CONTRACTS_DIR = Path(__file__).parent.parent.parent / "code" / "contracts"


class TestSchemaLoading:
    """Test that schema files can be loaded and are valid YAML."""

    @pytest.mark.parametrize("schema_file", [
        "diffusion_results.schema.yaml",
        "bootstrap_stats.schema.yaml",
        "sensitivity_report.schema.yaml",
    ])
    def test_schema_files_load_valid_yaml(self, schema_file):
        """Each schema file must be valid YAML."""
        schema_path = CONTRACTS_DIR / schema_file
        assert schema_path.exists(), f"Schema file not found: {schema_path}"

        with open(schema_path, "r") as f:
            schema = yaml.safe_load(f)

        assert isinstance(schema, dict), "Schema must be a dictionary"
        assert "$schema" in schema, "Schema must define $schema"
        assert "title" in schema, "Schema must have a title"
        assert "type" in schema, "Schema must define a type"
        assert "required" in schema, "Schema must define required fields"

    def test_schema_validator_can_load_diffusion_results(self):
        """Verify load_schema works for diffusion_results."""
        schema_path = CONTRACTS_DIR / "diffusion_results.schema.yaml"
        schema = load_schema(schema_path)
        assert schema is not None
        assert schema["title"] == "DiffusionResults"

    def test_schema_validator_can_load_bootstrap_stats(self):
        """Verify load_schema works for bootstrap_stats."""
        schema_path = CONTRACTS_DIR / "bootstrap_stats.schema.yaml"
        schema = load_schema(schema_path)
        assert schema is not None
        assert schema["title"] == "BootstrapStats"

    def test_schema_validator_can_load_sensitivity_report(self):
        """Verify load_schema works for sensitivity_report."""
        schema_path = CONTRACTS_DIR / "sensitivity_report.schema.yaml"
        schema = load_schema(schema_path)
        assert schema is not None
        assert schema["title"] == "SensitivityReport"


class TestSchemaValidation:
    """Test that valid artifacts pass validation and invalid ones fail."""

    def test_valid_diffusion_results_passes(self):
        """A valid diffusion result should pass validation."""
        schema_path = CONTRACTS_DIR / "diffusion_results.schema.yaml"
        valid_data = {
            "solvent": "water",
            "timescale": "10ns",
            "diffusion_coefficient": {
                "value": 2.30e-9,
                "unit": "m²/s"
            },
            "r_squared": 0.98,
            "linear_regression_params": {
                "slope": 1.38e-8,
                "intercept": 0.0,
                "std_err": 0.001
            },
            "scaling_factor_applied": 1.0,
            "validation_status": "passed",
            "timestamp": "2023-10-01T12:00:00Z",
            "source_files": ["traj.xtc"],
            "metadata": {"force_field": "MARTINI"}
        }
        result = validate_artifact(valid_data, schema_path)
        assert result["valid"], f"Valid data should pass: {result.get('errors')}"

    def test_invalid_diffusion_results_fails_missing_required(self):
        """Missing required field should fail validation."""
        schema_path = CONTRACTS_DIR / "diffusion_results.schema.yaml"
        invalid_data = {
            "solvent": "water",
            # Missing timescale, diffusion_coefficient, etc.
            "timestamp": "2023-10-01T12:00:00Z"
        }
        result = validate_artifact(invalid_data, schema_path)
        assert not result["valid"], "Invalid data should fail validation"
        assert len(result.get("errors", [])) > 0

    def test_invalid_diffusion_results_fails_enum(self):
        """Invalid enum value should fail validation."""
        schema_path = CONTRACTS_DIR / "diffusion_results.schema.yaml"
        invalid_data = {
            "solvent": "unknown_solvent",  # Not in enum
            "timescale": "10ns",
            "diffusion_coefficient": {
                "value": 2.30e-9,
                "unit": "m²/s"
            },
            "r_squared": 0.98,
            "linear_regression_params": {
                "slope": 1.38e-8,
                "intercept": 0.0,
                "std_err": 0.001
            },
            "scaling_factor_applied": 1.0,
            "validation_status": "passed",
            "timestamp": "2023-10-01T12:00:00Z",
            "source_files": ["traj.xtc"],
            "metadata": {}
        }
        result = validate_artifact(invalid_data, schema_path)
        assert not result["valid"], "Invalid enum should fail"

    def test_valid_bootstrap_stats_passes(self):
        """A valid bootstrap stats object should pass validation."""
        schema_path = CONTRACTS_DIR / "bootstrap_stats.schema.yaml"
        valid_data = {
            "solvent": "ethanol",
            "timescale": "5ns",
            "mean_mae": 0.15,
            "std_mae": 0.02,
            "ci_95_lower": 0.11,
            "ci_95_upper": 0.19,
            "n_iterations": 1000,
            "ci_method": "percentile",
            "fallback_triggered": False,
            "timestamp": "2023-10-01T12:00:00Z"
        }
        result = validate_artifact(valid_data, schema_path)
        assert result["valid"], f"Valid data should pass: {result.get('errors')}"

    def test_valid_sensitivity_report_passes(self):
        """A valid sensitivity report should pass validation."""
        schema_path = CONTRACTS_DIR / "sensitivity_report.schema.yaml"
        valid_data = {
            "solvent": "acetone",
            "timescale": "10ns",
            "total_trajectory_length": 10.0,
            "start_time_fractions": [0.1, 0.2, 0.3],
            "results": [
                {"start_fraction": 0.1, "diffusion_coefficient": 4.5e-9, "r_squared": 0.99},
                {"start_fraction": 0.2, "diffusion_coefficient": 4.4e-9, "r_squared": 0.98},
                {"start_fraction": 0.3, "diffusion_coefficient": 4.45e-9, "r_squared": 0.97}
            ],
            "variance_percentage": 1.2,
            "variance_passed": True,
            "timestamp": "2023-10-01T12:00:00Z"
        }
        result = validate_artifact(valid_data, schema_path)
        assert result["valid"], f"Valid data should pass: {result.get('errors')}"