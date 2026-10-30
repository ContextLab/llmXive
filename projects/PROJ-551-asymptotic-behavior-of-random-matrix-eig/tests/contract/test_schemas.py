"""
Contract-validation test suite (T001).

One test is provided for EACH artifact the pipeline is expected to
produce. Every test loads the REAL file from ``data/processed/`` and
validates it against the matching schema in ``contracts/`` (JSON Schema
via ``jsonschema`` for JSON files; explicit column-level checks for
Parquet/CSV). Missing files cause FAIL; there are no SKIP branches.
"""
import json
import pathlib
import yaml
import jsonschema
import pandas as pd
import pytest
from llmxive_toolkit import paths

REPO_ROOT = paths.root

def _load_schema(name: str) -> dict:
    schema_path = REPO_ROOT / "contracts" / f"{name}.schema.yaml"
    assert schema_path.is_file(), f"Schema file missing: {schema_path}"
    with schema_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _validate_json(path: pathlib.Path, schema_name: str) -> None:
    assert path.is_file(), f"Artifact missing: {path}"
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    schema = _load_schema(schema_name)
    jsonschema.validate(instance=data, schema=schema)

def test_single_run_results():
    path = paths.data("processed", "single_run_results.json")
    _validate_json(path, "single_run_results")

def test_convergence_report():
    path = paths.data("processed", "convergence_report.json")
    _validate_json(path, "convergence_report")

def test_sweep_runs_parquet():
    path = paths.data("processed", "sweep_runs.parquet")
    assert path.is_file(), f"Artifact missing: {path}"
    df = pd.read_parquet(path)
    required = {"N", "theta", "run_id", "outlier_flag"}
    missing = required - set(df.columns)
    assert not missing, f"Missing columns in sweep_runs.parquet: {missing}"
    assert len(df) > 0, "sweep_runs.parquet is empty"

def test_aggregated_thresholds():
    path = paths.data("processed", "aggregated_thresholds.json")
    _validate_json(path, "aggregated_thresholds")

def test_threshold_fit():
    path = paths.data("processed", "threshold_fit.json")
    _validate_json(path, "threshold_fit")

def test_sensitivity_density_sweep_parquet():
    path = paths.data("processed", "sensitivity_density_sweep.parquet")
    assert path.is_file(), f"Artifact missing: {path}"
    df = pd.read_parquet(path)
    required = {"N", "density", "theta", "run_id", "outlier_flag"}
    missing = required - set(df.columns)
    assert not missing, f"Missing columns in sensitivity_density_sweep.parquet: {missing}"
    assert len(df) > 0, "sensitivity_density_sweep.parquet is empty"

def test_sensitivity_metadata():
    path = paths.data("processed", "sensitivity_metadata.json")
    _validate_json(path, "sensitivity_metadata")

def test_sensitivity_variation_csv():
    path = paths.data("processed", "sensitivity_variation.csv")
    assert path.is_file(), f"Artifact missing: {path}"
    df = pd.read_csv(path)
    required = {"density", "mean_theta_c", "std_dev"}
    missing = required - set(df.columns)
    assert not missing, f"Missing columns in sensitivity_variation.csv: {missing}"
    assert len(df) > 0, "sensitivity_variation.csv is empty"
    assert df["mean_theta_c"].notna().all(), "mean_theta_c contains null values"

def test_sensitivity_variation_notes():
    path = paths.data("processed", "sensitivity_variation_notes.json")
    _validate_json(path, "sensitivity_variation_notes")

def test_finite_size_results_csv():
    path = paths.data("processed", "finite_size_results.csv")
    assert path.is_file(), f"Artifact missing: {path}"
    df = pd.read_csv(path)
    required = {"N", "k", "theta", "pattern_type", "empirical_bulk_edge", "outlier_probability"}
    missing = required - set(df.columns)
    assert not missing, f"Missing columns in finite_size_results.csv: {missing}"
    assert len(df) > 0, "finite_size_results.csv is empty"
    assert df["empirical_bulk_edge"].notna().all(), "empirical_bulk_edge contains nulls"
    assert df["outlier_probability"].notna().all(), "outlier_probability contains nulls"

def test_perturbation_verification():
    path = paths.data("processed", "perturbation_verification.json")
    _validate_json(path, "perturbation_verification")