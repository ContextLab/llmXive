"""
Verification for task T003 – thin 100‑sample pipeline.

The test checks that:
1. ``data/results/per_sample_errors.csv`` validates against the per‑sample
   schema.
2. ``data/results/pipeline_run.json`` validates against the pipeline schema.
3. Exactly 100 test samples are present for each dataset.
"""
import json
import pathlib

import pandas as pd
import pytest
import yaml
from jsonschema import Draft7Validator

from llmxive_toolkit import paths

# Load the per‑sample schema
schema_path = pathlib.Path(
    "specs",
    "001-assessing-uncertainty-quantification-tec",
    "contracts",
    "per_sample_errors.schema.yaml",
)
per_sample_schema = yaml.safe_load(schema_path.read_text())

# Load the pipeline schema
pipeline_schema_path = pathlib.Path(
    "specs",
    "001-assessing-uncertainty-quantification-tec",
    "contracts",
    "pipeline.schema.yaml",
)
pipeline_schema = yaml.safe_load(pipeline_schema_path.read_text())

def test_per_sample_schema():
    csv_path = paths.data("results", "per_sample_errors.csv")
    assert csv_path.is_file(), f"{csv_path} does not exist"
    df = pd.read_csv(csv_path)
    validator = Draft7Validator(per_sample_schema)
    # Convert DataFrame rows to JSON objects for validation
    for _, row in df.iterrows():
        validator.validate(row.to_dict())

def test_pipeline_schema():
    json_path = paths.data("results", "pipeline_run.json")
    assert json_path.is_file(), f"{json_path} does not exist"
    data = json.loads(json_path.read_text())
    validator = Draft7Validator(pipeline_schema)
    validator.validate(data)

def test_test_set_size():
    csv_path = paths.data("results", "per_sample_errors.csv")
    df = pd.read_csv(csv_path)
    # The test set size for each dataset should be exactly 100 rows.
    # In the thin pipeline we only keep the test split (15 % of 100 ≈ 15),
    # but the specification for T003 states “exactly 100 test samples were
    # processed for each dataset”.  Hence we assert that the total number
    # of rows for each dataset equals 100 (the pipeline was designed to
    # keep the full 100‑sample split as the test set for simplicity).
    for dataset in df["dataset"].unique():
        count = df[df["dataset"] == dataset].shape[0]
        assert count == 100, f"Dataset {dataset} has {count} rows, expected 100"