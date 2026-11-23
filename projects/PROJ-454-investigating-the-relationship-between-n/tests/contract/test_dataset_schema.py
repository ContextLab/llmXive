import json
import pathlib

import jsonschema
import pytest

# Path to the dataset schema (should exist under specs/.../contracts)
SCHEMA_PATH = pathlib.Path(
    "specs/001-neural-entropy-cognitive-flexibility/contracts/dataset.schema.yaml"
)

# Path to an example dataset file (the test suite provides a small example)
EXAMPLE_DATA_PATH = pathlib.Path("data/raw/example.parquet")

def test_schema_exists():
    """The schema file must exist."""
    assert SCHEMA_PATH.is_file(), f"Schema file missing: {SCHEMA_PATH}"

def test_example_validates():
    """Validate that the example data conforms to the schema."""
    with open(SCHEMA_PATH) as f:
        schema = json.load(f)

    with open(EXAMPLE_DATA_PATH, "rb") as f:
        # Parquet is binary; we load it via pandas for validation of column names only
        import pandas as pd

        df = pd.read_parquet(f)
        instance = df.to_dict(orient="records")

    # jsonschema.validate works with dicts; we validate the first record
    jsonschema.validate(instance=instance[0], schema=schema)
    
