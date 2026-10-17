"""
Test that the per-sample errors schema defines exactly the required columns.
This verifies the contract for `specs/001-assessing-uncertainty-quantification-tec/
contracts/per_sample_errors.schema.yaml`.
"""

import pathlib

import yaml
from llmxive_toolkit import paths

# Expected column names in the exact order defined by the specification
EXPECTED_COLUMNS = [
    "sample_id",
    "dataset",
    "method",
    "prediction",
    "lower_bound",
    "upper_bound",
    "ground_truth",
    "abs_error",
]


def test_per_sample_schema_columns():
    """
    Load the YAML schema and assert that the ``columns`` list matches the
    expected set (order is not important for validation, but we check both
    name and presence).
    """
    schema_path = paths.specs(
        "001-assessing-uncertainty-quantification-tec",
        "contracts",
        "per_sample_errors.schema.yaml",
    )
    assert schema_path.is_file(), f"Schema file not found: {schema_path}"

    with schema_path.open("r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    # The schema should contain a top‑level ``columns`` key with a list of dicts
    assert "columns" in schema, "Schema missing 'columns' key"
    column_entries = schema["columns"]
    assert isinstance(column_entries, list), "'columns' should be a list"

    # Extract column names from the dict entries
    column_names = [entry.get("name") for entry in column_entries]
    assert None not in column_names, "Some column entries lack a 'name' field"

    # Verify that the set matches exactly the expected columns
    assert set(column_names) == set(
        EXPECTED_COLUMNS
    ), f"Schema columns {column_names} do not match expected {EXPECTED_COLUMNS}"

    # Optional: ensure no extra columns are defined
    extra = set(column_names) - set(EXPECTED_COLUMNS)
    missing = set(EXPECTED_COLUMNS) - set(column_names)
    assert not extra, f"Unexpected extra columns in schema: {extra}"
    assert not missing, f"Missing required columns in schema: {missing}"

# The test will be discovered and run by pytest; exiting with no assertion
# failures signals success.