"""Contract test for the dataset schema.

This test validates that the processed dataset located at
``data/processed/dataset.parquet`` conforms to the JSON Schema
defined in ``contracts/dataset.schema.yaml``.  It checks that the
schema file exists, the dataset file exists, and that each row
(limited to the first 100 rows for speed) validates against the
schema using ``jsonschema``.
"""

import pathlib

import pandas as pd
import yaml
from jsonschema import validate, ValidationError


def _load_schema() -> dict:
    """Load the dataset JSON schema from the contracts directory."""
    project_root = pathlib.Path(__file__).resolve().parents[2]
    schema_path = project_root / "contracts" / "dataset.schema.yaml"
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_dataset() -> pd.DataFrame:
    """Load the processed dataset."""
    project_root = pathlib.Path(__file__).resolve().parents[2]
    dataset_path = project_root / "data" / "processed" / "dataset.parquet"
    if not dataset_path.is_file():
        raise FileNotFoundError(f"Dataset file not found at {dataset_path}")
    return pd.read_parquet(dataset_path)


def test_dataset_schema():
    """Validate the dataset against the contract schema."""
    schema = _load_schema()
    df = _load_dataset()

    # Validate a sample of rows to keep the test fast.
    sample = df.head(100)

    for idx, row in sample.iterrows():
        try:
            validate(instance=row.to_dict(), schema=schema)
        except ValidationError as exc:
            raise AssertionError(
                f"Row {idx} does not conform to schema: {exc.message}"
            ) from exc