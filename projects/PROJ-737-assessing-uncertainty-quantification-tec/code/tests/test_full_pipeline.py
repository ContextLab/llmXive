"""
Integration test for the full‑scale pipeline (Task T004).

The test validates that:
  * ``data/results/per_sample_errors.csv`` exists and conforms to the per‑sample schema.
  * ``data/results/uq_methods.csv`` contains an entry for every dataset‑method pair.
  * ``data/results/cost_metrics.csv`` is present and has the expected columns.
  * ``data/results/pipeline_log.csv`` contains a JSON object that validates against
    ``specs/001-assessing-uncertainty-quantification-tec/contracts/pipeline.schema.yaml``.
  * Each dataset provides at least 200 test samples (as required by the power‑analysis).
"""
import json
import pathlib

import pandas as pd
import yaml
from jsonschema import Draft7Validator

from llmxive_toolkit import paths

# ----------------------------------------------------------------------
# Helper: load and validate a CSV against a column‑order list
# ----------------------------------------------------------------------
def _validate_csv_columns(csv_path: pathlib.Path, expected_columns: list) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    missing = set(expected_columns) - set(df.columns)
    assert not missing, f"Missing columns {missing} in {csv_path.name}"
    # Ensure the column order matches the contract (optional but helpful)
    df = df[expected_columns]
    return df

# ----------------------------------------------------------------------
# Test definitions
# ----------------------------------------------------------------------
def test_pipeline_outputs():
    # 1. Per‑sample errors
    per_sample_path = paths.data("results", "per_sample_errors.csv")
    assert per_sample_path.is_file(), "per_sample_errors.csv not found"

    per_sample_cols = [
        "sample_id",
        "dataset",
        "method",
        "prediction",
        "lower_bound",
        "upper_bound",
        "ground_truth",
        "abs_error",
    ]
    per_df = _validate_csv_columns(per_sample_path, per_sample_cols)

    # Ensure each dataset‑method combo appears at least once
    datasets = per_df["dataset"].unique()
    methods = per_df["method"].unique()
    expected_pairs = {(d, m) for d in datasets for m in ["gpr", "mc_dropout", "deep_ensemble", "conformal"]}
    actual_pairs = set(zip(per_df["dataset"], per_df["method"]))
    missing_pairs = expected_pairs - actual_pairs
    assert not missing_pairs, f"Missing predictions for pairs: {missing_pairs}"

    # Verify at least 200 test samples per dataset
    for ds in datasets:
        count = per_df[per_df["dataset"] == ds].shape[0]
        assert count >= 200, f"Dataset {ds} has only {count} test samples (needs >=200)"

    # 2. UQ method registry
    uq_methods_path = paths.data("results", "uq_methods.csv")
    assert uq_methods_path.is_file(), "uq_methods.csv not found"
    uq_cols = ["method_id", "baseline_model", "hyperparams", "n_iterations", "status", "error_msg"]
    uq_df = _validate_csv_columns(uq_methods_path, uq_cols)

    # One row per dataset‑method
    assert len(uq_df) == len(datasets) * 4, "uq_methods.csv does not contain an entry for every dataset‑method pair"

    # All statuses should be either 'passed' or 'failed'
    assert set(uq_df["status"]).issubset({"passed", "failed"}), "Unexpected status values in uq_methods.csv"

    # 3. Cost metrics
    cost_path = paths.data("results", "cost_metrics.csv")
    assert cost_path.is_file(), "cost_metrics.csv not found"
    cost_cols = ["dataset_id", "method_id", "train_time_s", "inference_time_s", "peak_ram_mb"]
    cost_df = _validate_csv_columns(cost_path, cost_cols)

    # Ensure cost rows align with method registry
    merged = pd.merge(uq_df, cost_df, left_on="method_id", right_on="method_id", how="inner")
    assert merged.shape[0] == uq_df.shape[0], "Cost metrics missing for some method entries"

    # 4. Pipeline execution log (CSV with a single JSON cell)
    log_path = paths.data("results", "pipeline_log.csv")
    assert log_path.is_file(), "pipeline_log.csv not found"
    log_df = pd.read_csv(log_path)
    assert "run_id" in log_df.columns, "pipeline_log.csv does not contain expected columns"

    # The first cell should be a JSON string that validates against the schema
    log_json_str = log_df.iloc[0]["run_id"]
    # The whole row is a JSON representation; reconstruct the dict
    log_dict = json.loads(log_df.to_json(orient="records"))[0]

    # Load the JSON schema
    schema_path = pathlib.Path(__file__).parents[2] / "specs" / "001-assessing-uncertainty-quantification-tec" / "contracts" / "pipeline.schema.yaml"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(log_dict), key=lambda e: e.path)
    assert not errors, f"Pipeline log does not conform to schema: {errors}"