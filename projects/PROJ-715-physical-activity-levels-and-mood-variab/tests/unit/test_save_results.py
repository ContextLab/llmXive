import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the functions to test
from save_results import save_results_to_json, validate_results_schema, load_schema


@pytest.fixture
def sample_results():
    return {
        "metadata": {
            "timestamp": "2023-10-27T10:00:00Z",
            "version": "1.0",
            "analysis_type": "associational",
            "dataset_source": "StudentLife"
        },
        "models": {
            "mood_std_model": {
                "formula": "log_mood_std ~ total_steps + sleep + C(day_of_week) + baseline_affect",
                "outcome": "log_mood_std",
                "predictor": "total_steps",
                "fixed_effects": [
                    {
                        "term": "Intercept",
                        "estimate": 1.5,
                        "std_err": 0.1,
                        "p_value": 0.001,
                        "ci_lower": 1.3,
                        "ci_upper": 1.7
                    },
                    {
                        "term": "total_steps",
                        "estimate": -0.002,
                        "std_err": 0.0005,
                        "p_value": 0.03,
                        "ci_lower": -0.003,
                        "ci_upper": -0.001
                    }
                ],
                "convergence": True
            },
            "mean_mood_model": {
                "formula": "mean_mood ~ total_steps + sleep + C(day_of_week) + baseline_affect",
                "outcome": "mean_mood",
                "predictor": "total_steps",
                "fixed_effects": [
                    {
                        "term": "Intercept",
                        "estimate": 3.5,
                        "std_err": 0.2,
                        "p_value": 0.0001,
                        "ci_lower": 3.1,
                        "ci_upper": 3.9
                    },
                    {
                        "term": "total_steps",
                        "estimate": 0.0001,
                        "std_err": 0.0001,
                        "p_value": 0.4,
                        "ci_lower": -0.0001,
                        "ci_upper": 0.0003
                    }
                ],
                "convergence": True
            }
        },
        "diagnostics": {
            "residuals_vs_fitted_path": "figures/residuals.png",
            "shapiro_wilk_pvalue": 0.2,
            "breusch_pagan_pvalue": 0.5
        }
    }


@pytest.fixture
def valid_schema():
    return {
        "required": ["models", "diagnostics", "metadata"],
        "properties": {
            "models": {"type": "object"},
            "diagnostics": {"type": "object"},
            "metadata": {"type": "object", "properties": {"analysis_type": {"type": "string"}}}
        }
    }


@pytest.fixture
def invalid_schema_missing_key():
    return {
        "required": ["models", "diagnostics", "metadata", "missing_key"],
        "properties": {}
    }


@pytest.fixture
def invalid_schema_type_mismatch():
    return {
        "required": ["metadata"],
        "properties": {
            "metadata": {
                "type": "object",
                "properties": {
                    "analysis_type": {"type": "number"}  # Expecting string, but data has string
                }
            }
        }
    }


def test_save_results_to_json(tmp_path, sample_results):
    output_file = tmp_path / "test_results.json"
    save_results_to_json(sample_results, output_file)

    assert output_file.exists()
    with open(output_file, "r") as f:
        loaded = json.load(f)

    assert loaded == sample_results


def test_validate_results_schema_valid(sample_results, valid_schema):
    assert validate_results_schema(sample_results, valid_schema) is True


def test_validate_results_schema_missing_required(sample_results, invalid_schema_missing_key):
    assert validate_results_schema(sample_results, invalid_schema_missing_key) is False


def test_validate_results_schema_type_mismatch(sample_results, invalid_schema_type_mismatch):
    # The schema expects 'analysis_type' to be a number, but it is a string in sample_results
    # Our validator should catch this if we check the specific property type
    # Note: The current validator implementation checks if the value matches the schema type
    # For 'analysis_type' (string), schema says 'number', so it should fail.
    # However, our validator only checks the top level type of the property if it exists.
    # Let's trace: metadata exists. properties.metadata.properties.analysis_type exists.
    # expected_type = 'number'. results['metadata']['analysis_type'] is 'associational' (str).
    # isinstance(str, (int, float)) is False. So it should return False.
    assert validate_results_schema(sample_results, invalid_schema_type_mismatch) is False


def test_load_schema(tmp_path):
    schema_content = """
    required:
      - test
    properties:
      test:
        type: string
    """
    schema_file = tmp_path / "test_schema.yaml"
    schema_file.write_text(schema_content)

    schema = load_schema(schema_file)
    assert "required" in schema
    assert schema["required"] == ["test"]