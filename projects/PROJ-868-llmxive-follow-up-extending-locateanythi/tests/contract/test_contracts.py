"""
Contract validation tests for inference result files.

The schema file is located at
`specs/001-llmxive-follow-up-extending-locateanythi/contracts/inference_results.schema.yaml`.
The test loads the schema with jsonschema and validates each result file
produced by the pipeline.

Only the sanity‑run output (`data/results/sanity_global.parquet`) is
required for T005, but the test will also validate any other parquet files
that happen to exist under `data/results/`.
"""

import json
from pathlib import Path

import pandas as pd
import pytest
from jsonschema import Draft7Validator

# Resolve the location of the schema relative to the repository root.
SCHEMA_PATH = Path(__file__).parents[2] / "contracts" / "inference_results.schema.yaml"

@pytest.fixture(scope="module")
def validator():
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    return Draft7Validator(schema)

def test_parquet_files_conform_to_schema(validator):
    # Find all parquet files under data/results/
    results_dir = Path(__file__).parents[3] / "data" / "results"
    parquet_files = list(results_dir.rglob("*.parquet"))
    assert parquet_files, "No parquet result files found for contract validation."

    for pfile in parquet_files:
        df = pd.read_parquet(pfile)
        # Convert each row to a plain dict for validation.
        for _, row in df.iterrows():
            # jsonschema expects basic Python types.
            record = json.loads(row.to_json())
            validator.validate(record)