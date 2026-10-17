import pathlib
import yaml


def test_per_sample_schema():
    """
    Verify that the per‑sample errors schema lists exactly the required columns.
    """
    # Path to the schema file inside the specs folder
    schema_path = (
        pathlib.Path(__file__).parents[2]
        / "specs"
        / "001-assessing-uncertainty-quantification-tec"
        / "contracts"
        / "per_sample_errors.schema.yaml"
    )

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    # Extract column names from the schema
    column_names = {col["name"] for col in schema.get("columns", [])}

    expected = {
        "sample_id",
        "dataset",
        "method",
        "prediction",
        "lower_bound",
        "upper_bound",
        "ground_truth",
        "abs_error",
    }

    assert column_names == expected, f"Schema columns mismatch: {column_names} != {expected}"

if __name__ == "__main__":
    # Allow running the test directly without pytest
    test_per_sample_schema()
    print("Per‑sample schema validation passed.")