"""
Test that the per-sample errors schema defines exactly the required columns.
This validates the contract at:
specs/001-assessing-uncertainty-quantification-tec/contracts/per_sample_errors.schema.yaml
"""

import pathlib
import yaml

def test_per_sample_schema_columns():
    # Resolve the absolute path to the schema file relative to this test file
    schema_path = (
        pathlib.Path(__file__).resolve()
        .parents[3]  # go up from code/tests to project root
        / "specs"
        / "001-assessing-uncertainty-quantification-tec"
        / "contracts"
        / "per_sample_errors.schema.yaml"
    )

    # Load YAML
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    # Extract column names
    actual_columns = [col["name"] for col in schema.get("columns", [])]

    # Expected column set as defined in the specification
    expected_columns = [
        "sample_id",
        "dataset",
        "method",
        "prediction",
        "lower_bound",
        "upper_bound",
        "ground_truth",
        "abs_error",
    ]

    # Assert that the schema contains exactly the expected columns (order not important)
    assert set(actual_columns) == set(expected_columns), (
        f"Schema columns mismatch. Expected: {expected_columns}, "
        f"Found: {actual_columns}"
    )

# The test will be discovered and run by pytest; a successful run exits with code 0.