"""
Contract‑validation test suite for the project.

One test is provided for **each** artifact that the pipeline is expected
to produce.  The tests load the real file from ``data/processed`` (or the
appropriate location for Parquet/CSV) and validate it against the matching
schema in ``contracts/``.  Missing files raise an ``AssertionError`` – no
``skip`` branches are used, satisfying the “FAIL on missing” requirement.
"""
import json
import pathlib

import yaml
import jsonschema
import pandas as pd
import pytest

# -----------------------------------------------------------------
# Helper to locate the repository root (three levels up from this file)
# -----------------------------------------------------------------
REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]

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

# -----------------------------------------------------------------
# 1. single_run_results.json
def test_single_run_results():
    path = REPO_ROOT / "data" / "processed" / "single_run_results.json"
    _validate_json(path, "single_run_results")

# 2. convergence_report.json
def test_convergence_report():
    path = REPO_ROOT / "data" / "processed" / "convergence_report.json"
    _validate_json(path, "convergence_report")

# 3. sweep_runs.parquet
def test_sweep_runs_parquet():
    path = REPO_ROOT / "data" / "processed" / "sweep_runs.parquet"
    assert path.is_file(), f"Artifact missing: {path}"
    df = pd.read_parquet(path)
    required = {"N", "theta", "run_id", "outlier_flag"}
    missing = required - set(df.columns)
    assert not missing, f"Missing columns in sweep_runs.parquet: {missing}"
    assert len(df) > 0, "sweep_runs.parquet is empty"

# 4. aggregated_thresholds.json
def test_aggregated_thresholds():
    path = REPO_ROOT / "data" / "processed" / "aggregated_thresholds.json"
    _validate_json(path, "aggregated_thresholds")

# 5. threshold_fit.json
def test_threshold_fit():
    path = REPO_ROOT / "data" / "processed" / "threshold_fit.json"
    _validate_json(path, "threshold_fit")

# 6. sensitivity_density_sweep.parquet
def test_sensitivity_density_sweep_parquet():
    path = REPO_ROOT / "data" / "processed" / "sensitivity_density_sweep.parquet"
    assert path.is_file(), f"Artifact missing: {path}"
    df = pd.read_parquet(path)
    required = {"N", "density", "theta", "run_id", "outlier_flag"}
    missing = required - set(df.columns)
    assert not missing, f"Missing columns in sensitivity_density_sweep.parquet: {missing}"
    assert len(df) > 0, "sensitivity_density_sweep.parquet is empty"

# 7. sensitivity_metadata.json
def test_sensitivity_metadata():
    path = REPO_ROOT / "data" / "processed" / "sensitivity_metadata.json"
    _validate_json(path, "sensitivity_metadata")

# 8. sensitivity_variation.csv
def test_sensitivity_variation_csv():
    path = REPO_ROOT / "data" / "processed" / "sensitivity_variation.csv"
    assert path.is_file(), f"Artifact missing: {path}"
    df = pd.read_csv(path)
    required = {"density", "mean_theta_c", "std_dev"}
    missing = required - set(df.columns)
    assert not missing, f"Missing columns in sensitivity_variation.csv: {missing}"
    assert len(df) > 0, "sensitivity_variation.csv is empty"
    assert df["mean_theta_c"].notna().all(), "mean_theta_c contains null values"

# 9. sensitivity_variation_notes.json
def test_sensitivity_variation_notes():
    path = REPO_ROOT / "data" / "processed" / "sensitivity_variation_notes.json"
    _validate_json(path, "sensitivity_variation_notes")

# 10. finite_size_results.csv
def test_finite_size_results_csv():
    path = REPO_ROOT / "data" / "processed" / "finite_size_results.csv"
    assert path.is_file(), f"Artifact missing: {path}"
    df = pd.read_csv(path)
    required = {
        "N",
        "k",
        "theta",
        "pattern_type",
        "empirical_bulk_edge",
        "outlier_probability",
    }
    missing = required - set(df.columns)
    assert not missing, f"Missing columns in finite_size_results.csv: {missing}"
    assert len(df) > 0, "finite_size_results.csv is empty"
    assert df["empirical_bulk_edge"].notna().all(), "empirical_bulk_edge contains nulls"
    assert df["outlier_probability"].notna().all(), "outlier_probability contains nulls"

# 11. perturbation_verification.json (new contract)
def test_perturbation_verification():
    path = REPO_ROOT / "data" / "processed" / "perturbation_verification.json"
    _validate_json(path, "perturbation_verification")
