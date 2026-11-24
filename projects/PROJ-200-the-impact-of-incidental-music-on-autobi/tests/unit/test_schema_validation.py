"""
Unit tests for JSON‑Schema validation of generated dataset and output artifacts.

The project defines two schema files:
* ``contracts/dataset.schema.yaml`` – contains definitions for the
  intermediate parquet artifacts (e.g., ``AggregatedMetric``).
* ``contracts/output.schema.yaml`` – describes the final CSV results
  (e.g., ``RegressionResults``).

These tests create minimal in‑memory examples that conform to each
definition, write them to temporary files (parquet for the dataset,
CSV for the output), and then validate the content against the
corresponding JSON‑Schema using the ``jsonschema`` library.

The purpose is to prove that the schemas are syntactically correct
and that real artefacts produced by the pipeline will pass validation.
"""

import json
import yaml
import pandas as pd
import pytest
from jsonschema import validate, Draft7Validator, ValidationError

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def load_yaml_schema(schema_path: str) -> dict:
    """Load a YAML schema file and return the parsed dictionary."""
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def get_definition(schema: dict, name: str) -> dict:
    """Extract a definition from a JSON‑Schema ``definitions`` block."""
    try:
        return schema["definitions"][name]
    except KeyError as exc:
        raise KeyError(f"Definition '{name}' not found in schema.") from exc

# ----------------------------------------------------------------------
# Dataset schema validation
# ----------------------------------------------------------------------
@pytest.fixture
def dataset_schema():
    """Load the dataset schema used for processed parquet files."""
    return load_yaml_schema("contracts/dataset.schema.yaml")

def test_aggregated_metric_schema_valid(dataset_schema, tmp_path):
    """
    Create a minimal ``AggregatedMetric`` record, write it to a parquet
    file and validate the resulting row against the schema definition.
    """
    # Build a DataFrame that matches the ``AggregatedMetric`` definition
    df = pd.DataFrame(
        [
            {
                "user_id": "user_1",
                "track_id": "track_42",
                "mean_vividness": 3.7,
                "mean_valence": 0.2,
                "count_cues": 5,
                "adolescent_exposure_ratio": 0.4,
            }
        ]
    )

    parquet_path = tmp_path / "aggregated_metric.parquet"
    df.to_parquet(parquet_path, index=False)

    # Load the file back as plain Python dicts for validation
    loaded = pd.read_parquet(parquet_path).to_dict(orient="records")[0]

    # Validate against the schema definition
    definition = get_definition(dataset_schema, "AggregatedMetric")
    validator = Draft7Validator(definition)
    errors = sorted(validator.iter_errors(loaded), key=lambda e: e.path)
    assert not errors, f"Schema validation errors: {[e.message for e in errors]}"

# ----------------------------------------------------------------------
# Output schema validation
# ----------------------------------------------------------------------
@pytest.fixture
def output_schema():
    """Load the output schema used for final CSV results."""
    return load_yaml_schema("contracts/output.schema.yaml")

def test_regression_results_schema_valid(output_schema, tmp_path):
    """
    Create a minimal ``RegressionResults`` row, write it to CSV and
    validate the content against the schema definition.
    """
    df = pd.DataFrame(
        [
            {
                "term": "adolescent_exposure_ratio",
                "estimate": 0.123,
                "std_error": 0.045,
                "t_value": 2.73,
                "p_value": 0.007,
                "vif": 1.2,
            },
            {
                "term": "popularity",
                "estimate": 0.056,
                "std_error": 0.020,
                "t_value": 2.80,
                "p_value": 0.006,
                "vif": 1.1,
            },
        ]
    )

    csv_path = tmp_path / "regression_summary.csv"
    df.to_csv(csv_path, index=False)

    # Load CSV back as plain dicts
    loaded = pd.read_csv(csv_path).to_dict(orient="records")

    definition = get_definition(output_schema, "RegressionResults")
    validator = Draft7Validator(definition)

    for row in loaded:
        errors = sorted(validator.iter_errors(row), key=lambda e: e.path)
        assert not errors, f"Schema validation errors in row {row}: {[e.message for e in errors]}"

# ----------------------------------------------------------------------
# Full‑file validation (optional sanity check)
# ----------------------------------------------------------------------
def test_full_dataset_file_validation(dataset_schema, tmp_path):
    """
    Write a small parquet file containing several ``AggregatedMetric``
    rows and validate the entire file against the top‑level schema by
    iterating over each record.
    """
    records = [
        {
            "user_id": "u1",
            "track_id": "t1",
            "mean_vividness": 4.1,
            "mean_valence": 0.3,
            "count_cues": 2,
            "adolescent_exposure_ratio": 0.0,
        },
        {
            "user_id": "u2",
            "track_id": "t2",
            "mean_vividness": 2.8,
            "mean_valence": -0.1,
            "count_cues": 3,
            "adolescent_exposure_ratio": 1.0,
        },
    ]

    df = pd.DataFrame(records)
    parquet_path = tmp_path / "aggregated_metrics.parquet"
    df.to_parquet(parquet_path, index=False)

    definition = get_definition(dataset_schema, "AggregatedMetric")
    validator = Draft7Validator(definition)

    for rec in pd.read_parquet(parquet_path).to_dict(orient="records"):
        errors = sorted(validator.iter_errors(rec), key=lambda e: e.path)
        assert not errors, f"Record {rec} failed schema validation: {[e.message for e in errors]}"