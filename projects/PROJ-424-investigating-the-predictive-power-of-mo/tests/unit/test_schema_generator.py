"""
Unit tests for the Schema Generator (Task T010).

These tests verify that the schema generator produces valid YAML
and that the generated schemas match the expected structure.
"""
import os
import yaml
import pytest
from pathlib import Path
import sys

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.schema_generator import (
    generate_diffusion_results_schema,
    generate_bootstrap_stats_schema,
    generate_sensitivity_report_schema
)

class TestDiffusionResultsSchema:
    def test_schema_is_dict(self):
        schema = generate_diffusion_results_schema()
        assert isinstance(schema, dict)

    def test_schema_has_required_keys(self):
        schema = generate_diffusion_results_schema()
        required_keys = ["$schema", "title", "type", "properties", "required"]
        for key in required_keys:
            assert key in schema

    def test_required_properties_exist(self):
        schema = generate_diffusion_results_schema()
        required_props = [
            "experiment_id", "solvent", "timescale_ns", "force_field",
            "msd_r_squared", "diffusion_coefficient", "scaled_diffusion_coefficient",
            "nist_reference", "mae", "timestamp"
        ]
        for prop in required_props:
            assert prop in schema["properties"]

    def test_solvent_enum_values(self):
        schema = generate_diffusion_results_schema()
        solvent_prop = schema["properties"]["solvent"]
        assert "enum" in solvent_prop
        assert set(solvent_prop["enum"]) == {"water", "ethanol", "acetone"}

    def test_r_squared_constraints(self):
        schema = generate_diffusion_results_schema()
        r2_prop = schema["properties"]["msd_r_squared"]
        assert r2_prop["minimum"] == 0
        assert r2_prop["maximum"] == 1

class TestBootstrapStatsSchema:
    def test_schema_is_dict(self):
        schema = generate_bootstrap_stats_schema()
        assert isinstance(schema, dict)

    def test_required_properties_exist(self):
        schema = generate_bootstrap_stats_schema()
        required_props = [
            "experiment_id", "solvent", "timescale_ns", "bootstrap_iterations",
            "mae_mean", "mae_ci_lower", "mae_ci_upper", "ci_level", "timestamp"
        ]
        for prop in required_props:
            assert prop in schema["properties"]

    def test_fallback_property_exists(self):
        schema = generate_bootstrap_stats_schema()
        assert "fallback_triggered" in schema["properties"]

class TestSensitivityReportSchema:
    def test_schema_is_dict(self):
        schema = generate_sensitivity_report_schema()
        assert isinstance(schema, dict)

    def test_required_properties_exist(self):
        schema = generate_sensitivity_report_schema()
        required_props = [
            "experiment_id", "solvent", "timescale_ns", "start_time_percentages",
            "diffusion_coefficients", "variance_percentage", "passes_threshold", "timestamp"
        ]
        for prop in required_props:
            assert prop in schema["properties"]

    def test_array_properties(self):
        schema = generate_sensitivity_report_schema()
        assert schema["properties"]["start_time_percentages"]["type"] == "array"
        assert schema["properties"]["diffusion_coefficients"]["type"] == "array"

class TestSchemaYamlValidity:
    """Test that the generated YAML is valid and can be re-loaded."""
    
    def test_diffusion_schema_yaml_valid(self):
        schema = generate_diffusion_results_schema()
        yaml_str = yaml.dump(schema)
        reloaded = yaml.safe_load(yaml_str)
        assert reloaded == schema

    def test_bootstrap_schema_yaml_valid(self):
        schema = generate_bootstrap_stats_schema()
        yaml_str = yaml.dump(schema)
        reloaded = yaml.safe_load(yaml_str)
        assert reloaded == schema

    def test_sensitivity_schema_yaml_valid(self):
        schema = generate_sensitivity_report_schema()
        yaml_str = yaml.dump(schema)
        reloaded = yaml.safe_load(yaml_str)
        assert reloaded == schema