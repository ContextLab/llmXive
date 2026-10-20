"""
Contract test for the model‑metrics JSON schema.
"""
import json
import pathlib

import yaml
from jsonschema import Draft7Validator

def test_metrics_schema_validates_dummy():
    schema_path = pathlib.Path(__file__).resolve().parents[2] / "contracts" / "model_metrics.schema.yaml"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    # Minimal valid JSON that satisfies the required fields.
    dummy = {
        "dataset_checksum": "deadbeef",
        "seed": 42,
        "band_gap": {"r2_mean": 0.0, "r2_std": 0.0, "mae_mean": 0.0, "mae_std": 0.0, "rmse_mean": 0.0, "rmse_std": 0.0},
        "hardness": {"r2_mean": 0.0, "r2_std": 0.0, "mae_mean": 0.0, "mae_std": 0.0, "rmse_mean": 0.0, "rmse_std": 0.0},
        "rf_baseline": {
            "band_gap": {"r2_mean": 0.0, "r2_std": 0.0, "mae_mean": 0.0, "mae_std": 0.0, "rmse_mean": 0.0, "rmse_std": 0.0},
            "hardness": {"r2_mean": 0.0, "r2_std": 0.0, "mae_mean": 0.0, "mae_std": 0.0, "rmse_mean": 0.0, "rmse_std": 0.0},
        },
        "delta_vs_rf": {
            "band_gap": {"delta_r2": 0.0, "delta_mae": 0.0, "delta_rmse": 0.0},
            "hardness": {"delta_r2": 0.0, "delta_mae": 0.0, "delta_rmse": 0.0},
        },
    }

    validator = Draft7Validator(schema)
    validator.validate(dummy)