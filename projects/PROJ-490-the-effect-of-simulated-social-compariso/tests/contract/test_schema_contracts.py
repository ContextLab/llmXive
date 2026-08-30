"""
Contract tests for schema validation.
Ensures that the generated schemas (dataset, output, results) are valid JSON Schema
and can be loaded by the project's validation utilities.
"""
import os
import json
import pytest
from pathlib import Path

# Import the validator utility from the project
from utils.validators import load_schema, validate_json_against_schema

# Base paths
BASE_DIR = Path(__file__).parent.parent.parent
PROJECT_ROOT = BASE_DIR / "projects" / "PROJ-490-the-effect-of-simulated-social-compariso"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

# Schema file paths
DATASET_SCHEMA_PATH = CONTRACTS_DIR / "dataset.schema.yaml"
OUTPUT_SCHEMA_PATH = CONTRACTS_DIR / "output.schema.yaml"
RESULTS_SCHEMA_PATH = CONTRACTS_DIR / "results.schema.yaml"

# Sample valid data instances for testing
SAMPLE_DATASET = {
    "version": "1.0.0",
    "description": "Test dataset",
    "fields": [
        {
            "name": "participant_id",
            "type": "integer",
            "description": "ID",
            "required": True
        },
        {
            "name": "avatar_condition",
            "type": "category",
            "description": "Condition",
            "required": True,
            "categories": ["0", "1"]
        },
        {
            "name": "pre_self_esteem",
            "type": "float",
            "description": "Pre score",
            "required": True,
            "min": 0,
            "max": 30
        },
        {
            "name": "post_self_esteem",
            "type": "float",
            "description": "Post score",
            "required": True,
            "min": 0,
            "max": 30
        },
        {
            "name": "comparison_tendency",
            "type": "float",
            "description": "INCOM score",
            "required": True,
            "min": 0,
            "max": 100
        }
    ]
}

SAMPLE_OUTPUT = {
    "metadata": {
        "timestamp": "2023-10-27T10:00:00Z",
        "data_source": "data/raw/sample.csv",
        "data_source_type": "synthetic",
        "sample_size": 150
    },
    "coefficients": {
        "intercept": 12.5,
        "terms": [
            {
                "name": "avatar_condition",
                "estimate": 2.1,
                "std_error": 0.5,
                "t_stat": 4.2,
                "p_value": 0.001,
                "ci_lower": 1.1,
                "ci_upper": 3.1
            },
            {
                "name": "pre_self_esteem",
                "estimate": 0.8,
                "std_error": 0.1,
                "t_stat": 8.0,
                "p_value": 0.000,
                "ci_lower": 0.6,
                "ci_upper": 1.0
            }
        ]
    },
    "diagnostics": {
        "normality": {
            "test": "Shapiro-Wilk",
            "statistic": 0.98,
            "p_value": 0.45,
            "passed": True
        },
        "homoscedasticity": {
            "test": "Breusch-Pagan",
            "statistic": 1.2,
            "p_value": 0.27,
            "passed": True
        },
        "collinearity": {
            "method": "VIF",
            "terms": [
                {"name": "avatar_condition", "vif": 1.05, "flagged": False},
                {"name": "pre_self_esteem", "vif": 1.12, "flagged": False}
            ]
        }
    }
}

SAMPLE_RESULTS = {
    "project_info": {
        "project_id": "PROJ-490",
        "project_name": "Social Comparison Study",
        "version": "1.0.0"
    },
    "data_summary": {
        "source_path": "data/raw/sample.csv",
        "source_type": "synthetic",
        "n_participants": 150,
        "missing_ratio": 0.02,
        "variables_validated": True
    },
    "model_results": {
        "coefficients": SAMPLE_OUTPUT["coefficients"]["terms"],
        "diagnostics": SAMPLE_OUTPUT["diagnostics"],
        "interpretation": "Simulated Causal Effect"
    },
    "robustness_analysis": {
        "bootstrap_iterations": 1000,
        "ci_width_variance": 0.005,
        "stability_flag": True
    },
    "sensitivity_analysis": {
        "thresholds_tested": [0.01, 0.05, 0.10],
        "parameter_recovery_error": 0.05,
        "error_correction_applied": "Bonferroni"
    },
    "conclusion": {
        "summary": "Significant effect found.",
        "limitations": ["Synthetic data only"],
        "next_steps": ["Validate with real data"]
    }
}

@pytest.fixture
def dataset_schema():
    return load_schema(DATASET_SCHEMA_PATH)

@pytest.fixture
def output_schema():
    return load_schema(OUTPUT_SCHEMA_PATH)

@pytest.fixture
def results_schema():
    return load_schema(RESULTS_SCHEMA_PATH)

class TestDatasetSchema:
    def test_schema_file_exists(self):
        assert DATASET_SCHEMA_PATH.exists(), "dataset.schema.yaml not found"

    def test_schema_is_valid_yaml(self, dataset_schema):
        assert dataset_schema is not None
        assert "fields" in dataset_schema

    def test_schema_validates_sample_data(self, dataset_schema):
        # Convert sample to JSON string for the validator if needed, 
        # or pass dict if validator accepts dict. 
        # Assuming validator accepts dict or file path.
        try:
            validate_json_against_schema(SAMPLE_DATASET, dataset_schema)
        except Exception as e:
            pytest.fail(f"Sample dataset failed validation: {e}")

class TestOutputSchema:
    def test_schema_file_exists(self):
        assert OUTPUT_SCHEMA_PATH.exists(), "output.schema.yaml not found"

    def test_schema_is_valid_yaml(self, output_schema):
        assert output_schema is not None
        assert "coefficients" in output_schema["properties"]

    def test_schema_validates_sample_data(self, output_schema):
        try:
            validate_json_against_schema(SAMPLE_OUTPUT, output_schema)
        except Exception as e:
            pytest.fail(f"Sample output failed validation: {e}")

class TestResultsSchema:
    def test_schema_file_exists(self):
        assert RESULTS_SCHEMA_PATH.exists(), "results.schema.yaml not found"

    def test_schema_is_valid_yaml(self, results_schema):
        assert results_schema is not None
        assert "conclusion" in results_schema["properties"]

    def test_schema_validates_sample_data(self, results_schema):
        try:
            validate_json_against_schema(SAMPLE_RESULTS, results_schema)
        except Exception as e:
            pytest.fail(f"Sample results failed validation: {e}")

class TestSchemaIntegrity:
    def test_all_schemas_loadable(self):
        """Ensure all contract schemas can be loaded without error."""
        assert load_schema(DATASET_SCHEMA_PATH) is not None
        assert load_schema(OUTPUT_SCHEMA_PATH) is not None
        assert load_schema(RESULTS_SCHEMA_PATH) is not None