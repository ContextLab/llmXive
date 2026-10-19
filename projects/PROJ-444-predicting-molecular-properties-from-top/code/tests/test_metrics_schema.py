"""
Contract test for Task T006: Model-metrics schema compliance.

Validates ``reports/metrics/model_metrics.json`` against
``specs/001-predicting-molecular-properties-from-top/contracts/model_metrics.schema.yaml``
and additionally enforces the structural requirements of T005:
per-fold R2/RMSE, means, and feature_importance arrays for traditional
and topological descriptors.

Run:  pytest code/tests/test_metrics_schema.py
"""

import json
from pathlib import Path

import pytest
import yaml

try:
    import jsonschema
except ImportError:  # pragma: no cover - jsonschema is preinstalled
    jsonschema = None

PROJECT_ROOT = Path(__file__).resolve().parents[2]
METRICS_PATH = PROJECT_ROOT / "reports" / "metrics" / "model_metrics.json"
SCHEMA_PATH = (
    PROJECT_ROOT
    / "specs"
    / "001-predicting-molecular-properties-from-top"
    / "contracts"
    / "model_metrics.schema.yaml"
)

FEATURE_SETS = ("traditional", "topological", "combined")
MODELS = ("linear", "rf")


def _load_metrics() -> dict:
    if not METRICS_PATH.is_file():
        pytest.fail(
            f"model_metrics.json not found at {METRICS_PATH} - run T005 first."
        )
    with METRICS_PATH.open() as f:
        return json.load(f)


def _load_schema() -> dict:
    if not SCHEMA_PATH.is_file():
        pytest.fail(f"Schema file not found: {SCHEMA_PATH}")
    with SCHEMA_PATH.open() as f:
        schema = yaml.safe_load(f)
    assert isinstance(schema, dict), "Schema must be a YAML mapping"
    return schema


def _is_standard_json_schema(schema: dict) -> bool:
    """True if the YAML looks like a JSON Schema we can validate with."""
    keys = set(schema.keys())
    if any(k in keys for k in ("$schema", "type", "properties", "items", "required")):
        # A bare "required" list without "properties" is a custom contract,
        # not a JSON Schema document.
        if keys <= {"required"}:
            return False
        return True
    return False


def _iter_model_blocks(metrics: dict):
    """Yield (feature_set, model_type, metrics_block) triples.

    Supports both flat structure {feature_set: {r2_per_fold, ...}} and the
    nested structure produced by 04_model_training.py:
    {feature_set: {linear: {...}, rf: {...}}}.
    """
    for fs in FEATURE_SETS:
        assert fs in metrics, f"Missing top-level key '{fs}'"
        block = metrics[fs]
        assert isinstance(block, dict), f"'{fs}' must be a mapping"
        if all(m in block for m in MODELS):
            for m in MODELS:
                yield fs, m, block[m]
        else:
            yield fs, None, block


def test_schema_file_exists_and_is_valid_yaml():
    schema = _load_schema()
    # The contract must at minimum declare required top-level entries.
    required = schema.get("required", [])
    assert isinstance(required, list), "'required' must be a list"
    for key in FEATURE_SETS:
        assert key in required, f"Schema must require '{key}'"
    assert "feature_importance" in required, (
        "Schema must require 'feature_importance'"
    )


def test_metrics_validates_against_schema():
    schema = _load_schema()
    metrics = _load_metrics()

    if _is_standard_json_schema(schema) and jsonschema is not None:
        validator_cls = jsonschema.validators.validator_for(schema)
        validator_cls.check_schema(schema)
        errors = sorted(
            validator_cls(schema).iter_errors(metrics), key=lambda e: e.path
        )
        if errors:
            msgs = "; ".join(
                f"at {list(e.path)}: {e.message}" for e in errors[:10]
            )
            pytest.fail(f"model_metrics.json violates schema: {msgs}")
    else:
        # Custom contract: enforce the declared required keys manually.
        for key in schema.get("required", []):
            assert key in metrics, f"Missing required key '{key}'"
        props = schema.get("properties", {})
        if isinstance(props, dict):
            for key, spec in props.items():
                if key in metrics and isinstance(spec, dict):
                    expected_type = spec.get("type")
                    if expected_type == "array":
                        assert isinstance(metrics[key], list), (
                            f"'{key}' must be an array"
                        )
                    elif expected_type == "object":
                        assert isinstance(metrics[key], dict), (
                            f"'{key}' must be an object"
                        )


def test_metrics_has_required_top_level_keys():
    metrics = _load_metrics()
    for key in FEATURE_SETS:
        assert key in metrics, f"Missing top-level key '{key}'"
    assert "feature_importance" in metrics, "Missing 'feature_importance'"


def test_per_fold_metrics_present_and_numeric():
    metrics = _load_metrics()
    saw_any = False
    for fs, model, block in _iter_model_blocks(metrics):
        saw_any = True
        assert isinstance(block, dict), (
            f"Metrics block for {fs}/{model} must be a mapping"
        )
        for field in ("r2_per_fold", "rmse_per_fold"):
            assert field in block, f"Missing '{field}' in {fs}/{model}"
            vals = block[field]
            assert isinstance(vals, list), f"'{field}' must be a list in {fs}/{model}"
            assert len(vals) > 0, f"'{field}' is empty in {fs}/{model}"
            for v in vals:
                assert isinstance(v, (int, float)), (
                    f"Non-numeric {field} value {v!r} in {fs}/{model}"
                )
                assert v == v, f"NaN in {field} of {fs}/{model}"
        for field in ("r2_mean", "rmse_mean"):
            assert field in block, f"Missing '{field}' in {fs}/{model}"
            assert isinstance(block[field], (int, float)), (
                f"'{field}' must be numeric in {fs}/{model}"
            )
    assert saw_any, "No model metric blocks found"


def test_feature_importance_structure():
    metrics = _load_metrics()
    fi = metrics["feature_importance"]
    assert isinstance(fi, dict), "'feature_importance' must be a mapping"
    for key in ("traditional", "topological"):
        assert key in fi, f"Missing '{key}' in feature_importance"
        arr = fi[key]
        assert isinstance(arr, list), f"feature_importance['{key}'] must be a list"
        assert len(arr) > 0, f"feature_importance['{key}'] is empty"
        for v in arr:
            assert isinstance(v, (int, float)), (
                f"Non-numeric importance {v!r} in '{key}'"
            )


def test_metadata_records_seed_and_split():
    metrics = _load_metrics()
    meta = metrics.get("metadata")
    assert isinstance(meta, dict), "Missing 'metadata' block"
    assert meta.get("seed") == 42, "Seed must be 42 (FR-004)"
    assert meta.get("n_folds") == 5, "Must use 5-fold CV (FR-004)"
    assert meta.get("split_method") == "scaffold_based_5fold"
    assert meta.get("target_property") == "logP"


def test_durable_copy_matches_report():
    durable = PROJECT_ROOT / "data" / "results" / "model_metrics.json"
    if not durable.is_file():
        pytest.skip("Durable copy under data/results/ not present.")
    with durable.open() as f:
        durable_metrics = json.load(f)
    metrics = _load_metrics()
    assert durable_metrics == metrics, (
        "data/results/model_metrics.json differs from reports/metrics/model_metrics.json"
    )