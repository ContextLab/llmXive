"""Contract tests validating AnalysisResult objects against analysis.schema.yaml."""

import json
import yaml
import pytest
from pathlib import Path
from jsonschema import validate, ValidationError, Draft7Validator
import datetime

# Schema path relative to project root
SCHEMA_PATH = Path(__file__).parent.parent.parent / "contracts" / "analysis.schema.yaml"


def load_analysis_schema():
    """Load the analysis schema from YAML file."""
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)


def create_valid_analysis_result():
    """Create a minimal valid AnalysisResult object."""
    return {
        "analysis_id": "ANL-2024-AB-001",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "data_status": {
            "has_real_data": True,
            "source_type": "paired_real",
            "sample_count": 50
        },
        "correlations": {
            "pearson": {
                "clustering_vs_conductivity": {
                    "coefficient": -0.45,
                    "p_value": 0.001
                },
                "path_length_vs_conductivity": {
                    "coefficient": 0.32,
                    "p_value": 0.02
                },
                "lcc_fraction_vs_conductivity": {
                    "coefficient": -0.15,
                    "p_value": 0.25
                },
                "percolation_threshold_vs_conductivity": {
                    "coefficient": 0.05,
                    "p_value": 0.72
                }
            },
            "spearman": {
                "clustering_vs_conductivity": {
                    "coefficient": -0.48,
                    "p_value": 0.0008
                },
                "path_length_vs_conductivity": {
                    "coefficient": 0.29,
                    "p_value": 0.035
                },
                "lcc_fraction_vs_conductivity": {
                    "coefficient": -0.12,
                    "p_value": 0.31
                },
                "percolation_threshold_vs_conductivity": {
                    "coefficient": 0.08,
                    "p_value": 0.65
                }
            },
            "partial_correlations": [
                {
                    "metric": "clustering",
                    "controlled_variables": ["defect_density", "temperature"],
                    "coefficient": -0.42,
                    "p_value": 0.003
                }
            ]
        },
        "statistical_significance": {
            "raw_p_values": {
                "clustering": 0.001,
                "path_length": 0.02
            },
            "corrected_p_values": {
                "clustering": 0.004,
                "path_length": 0.08
            },
            "correction_method": "bonferroni",
            "significance_threshold": 0.05
        },
        "confidence_intervals": {
            "method": "bootstrap_percentile",
            "confidence_level": 0.95,
            "intervals": {
                "clustering_vs_conductivity": {
                    "lower_bound": -0.65,
                    "upper_bound": -0.25,
                    "bootstrap_samples": 1000
                },
                "path_length_vs_conductivity": {
                    "lower_bound": 0.05,
                    "upper_bound": 0.59,
                    "bootstrap_samples": 1000
                }
            }
        },
        "regression_models": [
            {
                "model_type": "linear",
                "metric": "clustering",
                "performance": {
                    "r_squared": 0.21,
                    "rmse": 12.5,
                    "adjusted_r_squared": 0.19
                },
                "hyperparameters": {}
            }
        ],
        "sensitivity_analysis": {
            "baseline_threshold": 2.0,
            "tested_multipliers": [1.0, 2.0, 2.5],
            "std_dev": 0.03,
            "pass_threshold": 0.05,
            "build_status": "pass"
        },
        "metadata": {
            "pipeline_version": "1.0.0",
            "config_snapshot": {
                "threshold": 2.0,
                "seed": 42,
                "statistical_override": False
            },
            "lattice_correction_applied": True,
            "r_lattice_used": 0.246,
            "notes": "Standard analysis run."
        },
        "warnings": []
    }


class TestAnalysisSchema:
    """Test suite for AnalysisResult schema validation."""

    @pytest.fixture
    def schema(self):
        """Load the analysis schema."""
        return load_analysis_schema()

    def test_schema_is_valid_yaml(self, schema):
        """Verify the schema file is valid YAML and is a dict."""
        assert isinstance(schema, dict)
        assert "$schema" in schema
        assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"

    def test_analysis_schema_validates_correct_data(self, schema):
        """Test that a valid AnalysisResult passes validation."""
        valid_result = create_valid_analysis_result()
        # Should not raise
        validate(instance=valid_result, schema=schema)

    def test_analysis_schema_rejects_missing_analysis_id(self, schema):
        """Test that missing analysis_id causes validation error."""
        invalid_result = create_valid_analysis_result()
        del invalid_result["analysis_id"]
        with pytest.raises(ValidationError):
            validate(instance=invalid_result, schema=schema)

    def test_analysis_schema_rejects_missing_timestamp(self, schema):
        """Test that missing timestamp causes validation error."""
        invalid_result = create_valid_analysis_result()
        del invalid_result["timestamp"]
        with pytest.raises(ValidationError):
            validate(instance=invalid_result, schema=schema)

    def test_analysis_schema_rejects_missing_data_status(self, schema):
        """Test that missing data_status causes validation error."""
        invalid_result = create_valid_analysis_result()
        del invalid_result["data_status"]
        with pytest.raises(ValidationError):
            validate(instance=invalid_result, schema=schema)

    def test_analysis_schema_handles_synthetic_data(self, schema):
        """Test that synthetic data status is valid."""
        result = create_valid_analysis_result()
        result["data_status"]["has_real_data"] = False
        result["data_status"]["source_type"] = "synthetic_validation"
        validate(instance=result, schema=schema)

    def test_analysis_schema_handles_unpaired_data(self, schema):
        """Test that unpaired data status is valid."""
        result = create_valid_analysis_result()
        result["data_status"]["source_type"] = "unpaired_real"
        result["data_status"]["sample_count"] = 150
        validate(instance=result, schema=schema)

    def test_analysis_schema_rejects_invalid_source_type(self, schema):
        """Test that invalid source_type causes validation error."""
        invalid_result = create_valid_analysis_result()
        invalid_result["data_status"]["source_type"] = "invalid_type"
        with pytest.raises(ValidationError):
            validate(instance=invalid_result, schema=schema)

    def test_analysis_schema_handles_null_correlation(self, schema):
        """Test that null correlation coefficients are handled correctly."""
        result = create_valid_analysis_result()
        # Some correlations can be null if data is insufficient
        result["correlations"]["pearson"]["lcc_fraction_vs_conductivity"]["coefficient"] = None
        # This should still validate if the schema allows null
        # Note: The schema defines coefficient as number, so null would fail.
        # This test documents expected behavior.
        with pytest.raises(ValidationError):
            validate(instance=result, schema=schema)

    def test_analysis_schema_validates_sensitivity_failure(self, schema):
        """Test that sensitivity failure status is valid."""
        result = create_valid_analysis_result()
        result["sensitivity_analysis"]["std_dev"] = 0.08
        result["sensitivity_analysis"]["build_status"] = "fail"
        validate(instance=result, schema=schema)

    def test_analysis_schema_rejects_invalid_correction_method(self, schema):
        """Test that invalid correction_method causes validation error."""
        invalid_result = create_valid_analysis_result()
        invalid_result["statistical_significance"]["correction_method"] = "invalid_method"
        with pytest.raises(ValidationError):
            validate(instance=invalid_result, schema=schema)

    def test_analysis_schema_validates_empty_warnings(self, schema):
        """Test that empty warnings array is valid."""
        result = create_valid_analysis_result()
        result["warnings"] = []
        validate(instance=result, schema=schema)

    def test_analysis_schema_validates_with_warnings(self, schema):
        """Test that warnings array with messages is valid."""
        result = create_valid_analysis_result()
        result["warnings"] = [
            "Low sample count for robust statistics",
            "One metric had insufficient variance"
        ]
        validate(instance=result, schema=schema)

    def test_schema_allows_additional_regression_models(self, schema):
        """Test that additional regression models are allowed."""
        result = create_valid_analysis_result()
        result["regression_models"].append({
            "model_type": "gaussian_process",
            "metric": "path_length",
            "performance": {
                "r_squared": 0.35,
                "rmse": 9.2,
                "adjusted_r_squared": 0.33
            },
            "hyperparameters": {
                "kernel": "RBF",
                "length_scale": 1.5
            }
        })
        validate(instance=result, schema=schema)

    def test_schema_validates_partial_correlations(self, schema):
        """Test that partial correlations are valid."""
        result = create_valid_analysis_result()
        result["correlations"]["partial_correlations"].append({
            "metric": "path_length",
            "controlled_variables": ["defect_density"],
            "coefficient": 0.28,
            "p_value": 0.04
        })
        validate(instance=result, schema=schema)