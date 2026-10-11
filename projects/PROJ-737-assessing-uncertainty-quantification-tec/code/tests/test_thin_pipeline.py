"""
Test suite for the thin pipeline (T003).

It validates that:
- The per‑sample errors CSV conforms to the schema.
- The pipeline run JSON conforms to its schema.
- Exactly 100 test samples are processed for each dataset.
"""

import json
import pathlib

import pandas as pd
import pytest
import yaml
from jsonschema import validate

# Paths
PER_SAMPLE_PATH = pathlib.Path("data/results/per_sample_errors.csv")
PIPELINE_LOG_PATH = pathlib.Path("data/results/pipeline_run.json")
SCHEMA_PER_SAMPLE = pathlib.Path(
    "specs/001-assessing-uncertainty-quantification-tec/contracts/per_sample_errors.schema.yaml"
)
SCHEMA_PIPELINE = pathlib.Path(
    "specs/001-assessing-uncertainty-quantification-tec/contracts/pipeline.schema.yaml"
)

def load_yaml_schema(path):
    return yaml.safe_load(path.read_text())

def test_per_sample_schema():
    schema = load_yaml_schema(SCHEMA_PER_SAMPLE)
    df = pd.read_csv(PER_SAMPLE_PATH)
    # Verify required columns exist
    required_cols = {col["name"] for col in schema["columns"]}
    assert required_cols.issubset(set(df.columns)), "Missing required columns"
    # Verify dtypes
    for col in schema["columns"]:
        name = col["name"]
        dtype = col["dtype"]
        # pandas dtypes may be object, float64, etc.
        assert str(df[name].dtype) == dtype, f"Column {name} has dtype {df[name].dtype}, expected {dtype}"

def test_pipeline_schema():
    schema = load_yaml_schema(SCHEMA_PIPELINE)
    data = json.loads(PIPELINE_LOG_PATH.read_text())
    validate(instance=data, schema=schema)

def test_test_sample_count():
    df = pd.read_csv(PER_SAMPLE_PATH)
    # Count test samples per dataset (method 'xgboost' is baseline, but all methods have same test set size)
    for dataset_id in df["dataset"].unique():
        subset = df[df["dataset"] == dataset_id]
        # Assuming each method contributes the same number of rows; divide by number of methods
        n_methods = subset["method"].nunique()
        n_rows = len(subset)
        test_samples = n_rows // n_methods
        assert test_samples == 100, f"Dataset {dataset_id} has {test_samples} test samples, expected 100"