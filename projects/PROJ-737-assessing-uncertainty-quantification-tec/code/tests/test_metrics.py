"""
Test suite for the metrics generation script (T005).

The test checks:
  1. The ``metrics_raw.csv`` file exists.
  2. Every row conforms to the JSON‑Schema contract defined in
     ``specs/001-assessing-uncertainty-quantification-tec/contracts/metrics.schema.yaml``.
  3. All four UQ methods are present for each of the three datasets.
  4. The ``timestamp`` column contains a valid ISO‑8601 datetime string.
"""

import json
import pathlib
from datetime import datetime

import pandas as pd
import yaml
from jsonschema import Draft7Validator

from llmxive_toolkit import paths

def test_metrics_file_exists():
    csv_path = paths.data("results", "metrics_raw.csv")
    assert csv_path.is_file(), f"Metrics file not found at {csv_path}"

def test_schema_compliance():
    csv_path = paths.data("results", "metrics_raw.csv")
    df = pd.read_csv(csv_path)

    schema_path = pathlib.Path(
        paths.root,
        "specs",
        "001-assessing-uncertainty-quantification-tec",
        "contracts",
        "metrics.schema.yaml",
    )
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    validator = Draft7Validator(schema)
    records = df.to_dict(orient="records")
    errors = list(validator.iter_errors(records))
    assert not errors, f"Schema validation errors: {[e.message for e in errors]}"

def test_coverage_of_all_combinations():
    csv_path = paths.data("results", "metrics_raw.csv")
    df = pd.read_csv(csv_path)

    # Expected identifiers
    expected_datasets = {"band_gap", "formation_energy", "thermal_conductivity"}
    expected_methods = {"gpr", "mc_dropout", "deep_ensemble", "conformal"}
    expected_metric_types = {"calibration_error", "sharpness", "coverage_error"}

    # Verify that each (dataset, method) pair appears exactly once for each metric type
    for dataset in expected_datasets:
        for method in expected_methods:
            subset = df[(df["dataset_id"] == dataset) & (df["method_id"] == method)]
            assert not subset.empty, f"Missing metrics for {dataset}/{method}"
            assert set(subset["metric_type"]) == expected_metric_types, (
                f"Metric types missing for {dataset}/{method}: "
                f"{expected_metric_types - set(subset['metric_type'])}"
            )

def test_timestamp_is_iso8601():
    csv_path = paths.data("results", "metrics_raw.csv")
    df = pd.read_csv(csv_path)

    for ts in df["timestamp"]:
        # datetime.fromisoformat accepts both 'Z' and offset forms in Python 3.11
        try:
            datetime.fromisoformat(ts)
        except Exception as exc:
            raise AssertionError(f"Invalid ISO‑8601 timestamp '{ts}': {exc}")
