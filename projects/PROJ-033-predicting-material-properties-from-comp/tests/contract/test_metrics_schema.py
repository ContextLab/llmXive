"""Contract tests for contracts/model_metrics.schema.yaml."""

from pathlib import Path

import yaml
from jsonschema import Draft7Validator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "model_metrics.schema.yaml"

METRIC_KEYS = ["r2_mean", "r2_std", "mae_mean", "mae_std",
               "rmse_mean", "rmse_std"]


def load_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def valid_metrics():
    def target_block():
        return {k: 0.5 for k in METRIC_KEYS}

    return {
        "dataset_checksum": "a" * 64,
        "seed": 42,
        "band_gap": target_block(),
        "hardness": target_block(),
        "rf_baseline": {"band_gap": target_block(),
                        "hardness": target_block()},
        "delta_vs_rf": {
            "band_gap": {"delta_r2": 0.1, "delta_mae": -0.05,
                         "delta_rmse": -0.05},
            "hardness": {"delta_r2": 0.05, "delta_mae": 1.2,
                         "delta_rmse": 1.5},
        },
    }


def test_schema_file_exists_and_parses():
    assert SCHEMA_PATH.exists(), f"missing schema: {SCHEMA_PATH}"
    schema = load_schema()
    Draft7Validator.check_schema(schema)


def test_schema_requires_top_level_blocks():
    schema = load_schema()
    required = set(schema["required"])
    assert required == {
        "dataset_checksum", "seed", "band_gap", "hardness",
        "rf_baseline", "delta_vs_rf",
    }
    assert schema.get("additionalProperties") is False


def test_valid_metrics_document_passes():
    validator = Draft7Validator(load_schema())
    errors = list(validator.iter_errors(valid_metrics()))
    assert not errors, f"unexpected errors: {errors}"


def test_missing_required_block_fails():
    validator = Draft7Validator(load_schema())
    for field in ["dataset_checksum", "seed", "band_gap", "hardness",
                  "rf_baseline", "delta_vs_rf"]:
        doc = valid_metrics()
        del doc[field]
        errors = list(validator.iter_errors(doc))
        assert errors, f"doc missing {field} should fail validation"


def test_missing_metric_key_fails():
    validator = Draft7Validator(load_schema())
    for key in METRIC_KEYS:
        doc = valid_metrics()
        del doc["band_gap"][key]
        errors = list(validator.iter_errors(doc))
        assert errors, f"band_gap block missing {key} should fail"


def test_wrong_types_fail():
    validator = Draft7Validator(load_schema())
    bad_docs = [
        {**valid_metrics(), "seed": "forty-two"},
        {**valid_metrics(), "dataset_checksum": 12345},
        {**valid_metrics(),
         "band_gap": {**valid_metrics()["band_gap"], "r2_mean": "high"}},
    ]
    for doc in bad_docs:
        errors = list(validator.iter_errors(doc))
        assert errors, f"doc {doc} should fail validation"
