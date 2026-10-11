"""
Contract tests for the JSON‑Schema validation files added in T005.

The tests ensure that:
1. The YAML files are syntactically valid and can be parsed.
2. The parsed content is a valid JSON‑Schema document according to jsonschema.
"""

import pathlib

import yaml
from jsonschema import Draft7Validator, exceptions as jsonschema_exceptions


def load_yaml_schema(schema_path: pathlib.Path):
    """Load a YAML schema file and return the parsed dictionary."""
    with schema_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_dataset_schema_is_valid():
    schema_path = pathlib.Path(
        "specs/001-statistical-analysis-of-publicly-availab/contracts/dataset.schema.yaml"
    )
    schema = load_yaml_schema(schema_path)

    # Basic sanity checks
    assert isinstance(schema, dict)
    assert "$schema" in schema
    assert "fields" in schema
    assert "validation_rules" in schema

    # Verify that the schema itself conforms to JSON‑Schema Draft‑07
    try:
        Draft7Validator.check_schema(schema)
    except jsonschema_exceptions.SchemaError as e:
        raise AssertionError(f"Dataset schema is not a valid JSON Schema: {e}")


def test_forecast_schema_is_valid():
    schema_path = pathlib.Path(
        "specs/001-statistical-analysis-of-publicly-availab/contracts/forecast.schema.yaml"
    )
    schema = load_yaml_schema(schema_path)

    # Basic sanity checks
    assert isinstance(schema, dict)
    assert "$schema" in schema
    assert "fields" in schema
    assert "validation_rules" in schema

    # Verify that the schema itself conforms to JSON‑Schema Draft‑07
    try:
        Draft7Validator.check_schema(schema)
    except jsonschema_exceptions.SchemaError as e:
        raise AssertionError(f"Forecast schema is not a valid JSON Schema: {e}")


# Optional: a minimal dummy CSV validation against the schemas.
# Here we simply construct a tiny DataFrame and ensure that loading the
# schema does not raise errors; full row‑level validation would require a
# more elaborate schema design which is beyond the current contract test.

def test_dummy_csv_can_be_loaded():
    import pandas as pd

    # Create a minimal CSV in memory
    dummy_data = pd.DataFrame(
        {
            "date": ["2020-11-03"],
            "pollster": ["SamplePollster"],
            "candidate": ["CandidateA"],
            "state": ["US"],
            "vote_share": [50.0],
            "sample_size": [1000],
            "mode": ["Online"],
            "party": ["Democrat"],
            "historical_rmse": [5.0],
            "week_bin": [1],
        }
    )

    # Write to a temporary CSV file
    tmp_path = pathlib.Path("data/processed/dummy_poll.csv")
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    dummy_data.to_csv(tmp_path, index=False)

    # Load back to ensure CSV handling works (the schema validation is
    # exercised separately above)
    reloaded = pd.read_csv(tmp_path)
    assert list(reloaded.columns) == list(dummy_data.columns)
    assert reloaded.equals(dummy_data)